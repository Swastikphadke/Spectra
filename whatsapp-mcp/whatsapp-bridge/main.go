package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"github.com/gin-gonic/gin"
	_ "github.com/mattn/go-sqlite3"
	"github.com/mdp/qrterminal/v3"
	"go.mau.fi/whatsmeow"
	waProto "go.mau.fi/whatsmeow/binary/proto" // ✅ FIX: Correct Import for Messages
	"go.mau.fi/whatsmeow/store/sqlstore"
	"go.mau.fi/whatsmeow/types"
	"go.mau.fi/whatsmeow/types/events"
	waLog "go.mau.fi/whatsmeow/util/log"
	"google.golang.org/protobuf/proto"
)

var client *whatsmeow.Client

func main() {
	ctx := context.Background()

	dbLog := waLog.Stdout("Database", "INFO", true)

	// ✅ FIX: Standard connection string
	container, err := sqlstore.New(ctx, "sqlite3", "file:session.db?_foreign_keys=on", dbLog)
	if err != nil {
		panic(err)
	}

	deviceStore, err := container.GetFirstDevice(ctx)
	if err != nil {
		panic(err)
	}

	clientLog := waLog.Stdout("Client", "INFO", true)
	client = whatsmeow.NewClient(deviceStore, clientLog)
	client.AddEventHandler(eventHandler)

	if client.Store.ID == nil {
		qrChan, _ := client.GetQRChannel(context.Background())
		err = client.Connect()
		if err != nil {
			panic(err)
		}
		for evt := range qrChan {
			if evt.Event == "code" {
				fmt.Println("Please scan this QR code with WhatsApp → Linked devices:")
				// Render a scannable QR in the terminal
				qrterminal.GenerateHalfBlock(evt.Code, qrterminal.L, os.Stdout)
				// Also print the raw code as a fallback (some terminals don't render well)
				fmt.Println("(fallback code)")
				fmt.Println(evt.Code)
			} else {
				fmt.Println("Login event:", evt.Event)
			}
		}
	} else {
		err = client.Connect()
		if err != nil {
			panic(err)
		}
	}

	fmt.Println("\n✓ Connected to WhatsApp! Type 'help' for commands.")

	// Start REST API
	r := gin.Default()
	r.POST("/api/send", sendMessageHandler)
	r.POST("/api/send_audio", sendAudioHandler)

	go func() {
		fmt.Println("Starting REST API server on :8080...")
		if err := r.Run(":8080"); err != nil {
			fmt.Println("Server error:", err)
		}
	}()

	// Wait for interrupt signal
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	<-c

	client.Disconnect()
	fmt.Println("\n🛑 Disconnected.")
}

func normalizeRecipient(raw string) string {
	recipient := strings.TrimSpace(raw)
	recipient = strings.TrimPrefix(recipient, "whatsapp:")
	recipient = strings.TrimPrefix(recipient, "+")
	recipient = strings.TrimSpace(recipient)
	return recipient
}

func parseRecipientJID(raw string) (types.JID, error) {
	recipient := normalizeRecipient(raw)
	if recipient == "" {
		return types.JID{}, errors.New("missing recipient")
	}

	// IMPORTANT:
	// - Plain phone numbers must be treated as user@DefaultUserServer (s.whatsapp.net)
	// - WhatsMeow AD-JIDs include ':' (specific device); let ParseJID handle those
	if strings.Contains(recipient, ":") {
		return types.ParseJID(recipient)
	}

	if strings.Contains(recipient, "@") {
		parts := strings.SplitN(recipient, "@", 2)
		user := strings.TrimSpace(parts[0])
		server := strings.TrimSpace(parts[1])
		if user == "" {
			return types.JID{}, errors.New("invalid jid: missing user")
		}
		if server == "" {
			server = types.DefaultUserServer
		}
		return types.NewJID(user, server), nil
	}

	// No '@' -> treat as phone number
	return types.NewJID(recipient, types.DefaultUserServer), nil
}

func eventHandler(evt interface{}) {
	switch msg := evt.(type) {
	case *events.Message:
		if msg.Info.IsFromMe {
			return
		}

		// ✅ FIX: Handle Linked Devices (LID) & Normal Numbers
		effectiveUser := msg.Info.Chat.User
		senderJID := msg.Info.Sender.String() // The specific device to reply to

		content := ""
		mediaType := ""

		if msg.Message.Conversation != nil {
			content = *msg.Message.Conversation
		} else if msg.Message.ExtendedTextMessage != nil {
			content = *msg.Message.ExtendedTextMessage.Text
		} else if msg.Message.AudioMessage != nil {
			mediaType = "audio"
			content = "[Audio Message]"
		}

		if content == "" {
			return
		}

		fmt.Printf("📩 [BRIDGE] Received from %s: %s\n", effectiveUser, content)

		// Send to Python Backend
		payload := map[string]string{
			"from":       "whatsapp:+" + effectiveUser,
			"sender_jid": senderJID,
			"content":    content,
			"type":       "text",
		}
		if mediaType != "" {
			payload["type"] = mediaType
		}

		jsonData, _ := json.Marshal(payload)

		// Fire Webhook
		go func() {
			resp, err := http.Post("http://localhost:8000/whatsapp-webhook", "application/json", bytes.NewBuffer(jsonData))
			if err != nil {
				fmt.Printf("❌ [BRIDGE] Webhook Failed: %v\n", err)
			} else {
				fmt.Printf("✅ [BRIDGE] Sent to Backend: %s\n", resp.Status)
				resp.Body.Close()
			}
		}()
	}
}

func sendMessageHandler(c *gin.Context) {
	var req struct {
		Recipient string `json:"recipient"`
		Message   string `json:"message"`
	}

	if err := c.BindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}

	// Normalize recipient (backend may send e.g. "whatsapp:+15551234567")
	jid, err := parseRecipientJID(req.Recipient)
	fmt.Printf("📤 [BRIDGE] /api/send recipient=%q -> jid=%s (server=%s)\n", req.Recipient, jid.String(), jid.Server)

	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JID format"})
		return
	}

	// ✅ FIX: Use waProto.Message (New Library Format)
	_, err = client.SendMessage(context.Background(), jid, &waProto.Message{
		Conversation: &req.Message,
	})

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return

	}

	c.JSON(http.StatusOK, gin.H{"status": "sent"})
}

func sendAudioHandler(c *gin.Context) {
	recipientRaw := c.PostForm("recipient")
	if recipientRaw == "" {
		recipientRaw = c.PostForm("phone")
	}

	if normalizeRecipient(recipientRaw) == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Missing recipient"})
		return
	}

	fileHeader, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Missing file"})
		return
	}

	file, err := fileHeader.Open()
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to open file"})
		return
	}
	defer file.Close()

	data, err := io.ReadAll(file)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to read file"})
		return
	}

	jid, err := parseRecipientJID(recipientRaw)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JID format"})
		return
	}

	isVoiceNote := strings.EqualFold(c.PostForm("is_voice_note"), "true") || c.PostForm("is_voice_note") == "1"

	up, err := client.Upload(context.Background(), data, whatsmeow.MediaAudio)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	mime := fileHeader.Header.Get("Content-Type")
	if mime == "" {
		mime = "audio/ogg"
	}

	audioMsg := &waProto.AudioMessage{
		Mimetype:      proto.String(mime),
		URL:           &up.URL,
		DirectPath:    &up.DirectPath,
		MediaKey:      up.MediaKey,
		FileEncSHA256: up.FileEncSHA256,
		FileSHA256:    up.FileSHA256,
		FileLength:    &up.FileLength,
		PTT:           proto.Bool(isVoiceNote),
	}

	_, err = client.SendMessage(context.Background(), jid, &waProto.Message{AudioMessage: audioMsg})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "sent"})
}

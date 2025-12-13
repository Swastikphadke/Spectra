import React from 'react';
import { Loader2, Sprout, CloudSun } from 'lucide-react';

const SpectraLoader = () => {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm">
      <div className="relative flex flex-col items-center">
        {/* Animated Icons Container */}
        <div className="relative h-24 w-24">
          {/* Spinning Outer Ring */}
          <div className="absolute inset-0 animate-spin-slow rounded-full border-4 border-green-100 border-t-green-600"></div>
          
          {/* Bouncing Center Icon */}
          <div className="absolute inset-0 flex items-center justify-center animate-bounce">
            <Sprout className="h-10 w-10 text-green-600" />
          </div>
          
          {/* Floating Weather Icon */}
          <div className="absolute -right-4 -top-4 animate-pulse">
            <CloudSun className="h-8 w-8 text-yellow-500" />
          </div>
        </div>

        {/* Loading Text */}
        <div className="mt-8 text-center">
          <h3 className="text-xl font-bold text-green-800">Spectra is thinking...</h3>
          <p className="mt-2 text-sm text-gray-600 animate-pulse">
            Analyzing soil data & satellite feeds 🛰️
          </p>
        </div>
      </div>
    </div>
  );
};

export default SpectraLoader;
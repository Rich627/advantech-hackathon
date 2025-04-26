// app/components/Navigation.tsx
"use client";
import React from 'react';

interface NavigationProps {
  onPrev?: () => void;
  onNext?: () => void;
  showPrev?: boolean;
  showNext?: boolean;
  position?: 'overlay' | 'bottom';
}

const Navigation = ({ 
  onPrev, 
  onNext, 
  showPrev = true, 
  showNext = true,
  position = 'bottom'
}: NavigationProps) => {
  
  if (position === 'overlay') {
    return (
      <div className="absolute inset-0 flex items-center justify-between pointer-events-none">
        {showPrev ? (
          <button 
            onClick={onPrev} 
            className="w-10 h-10 flex items-center justify-center rounded-full bg-white border border-gray-300 shadow-md pointer-events-auto"
          >
            <span className="text-2xl">&larr;</span>
          </button>
        ) : <div className="w-10"></div>}
        
        {showNext ? (
          <button 
            onClick={onNext} 
            className="w-10 h-10 flex items-center justify-center rounded-full bg-white border border-gray-300 shadow-md pointer-events-auto"
          >
            <span className="text-2xl">&rarr;</span>
          </button>
        ) : <div className="w-10"></div>}
      </div>
    );
  }
  
  return (
    <div className="flex justify-between items-center w-full mt-4">
      {showPrev ? (
        <button 
          onClick={onPrev} 
          className="w-10 h-10 flex items-center justify-center rounded-full bg-white border border-gray-300"
        >
          <span className="text-2xl">&larr;</span>
        </button>
      ) : <div className="w-10"></div>}
      
      {showNext ? (
        <button 
          onClick={onNext} 
          className="w-10 h-10 flex items-center justify-center rounded-full bg-white border border-gray-300"
        >
          <span className="text-2xl">&rarr;</span>
        </button>
      ) : <div className="w-10"></div>}
    </div>
  );
};

export default Navigation;
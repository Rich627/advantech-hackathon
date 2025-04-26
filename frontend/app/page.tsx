// app/page.tsx
"use client";
import React, { useState } from 'react';
import Header from './components/Header';
import CrackCard from './components/CrackCard';
import Navigation from './components/Navigation';

// Mock data - imagine this coming from an API
const allCracks = [
  // Page 1
  [
    { id: '1', imageSrc: '/images/crack1.jpg' },
    { id: '2', imageSrc: '/images/crack1.jpg' },
    { id: '3', imageSrc: '/images/crack1.jpg' },
  ],
  // Page 2
  [
    { id: '4', imageSrc: '/images/crack1.jpg' },
    { id: '5', imageSrc: '/images/crack1.jpg' },
    { id: '6', imageSrc: '/images/crack1.jpg' },
  ],
  // Page 3
  [
    { id: '7', imageSrc: '/images/crack1.jpg' },
    { id: '8', imageSrc: '/images/crack1.jpg' },
    { id: '9', imageSrc: '/images/crack1.jpg' },
  ]
];

export default function Home() {
  const [currentPage, setCurrentPage] = useState(0);
  const totalPages = allCracks.length;
  
  const handlePrev = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };
  
  const handleNext = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1);
    }
  };

  return (
    <div>
      <Header />
      <main className="p-6">
        <div className="flex flex-col items-center">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {allCracks[currentPage].map((crack) => (
              <CrackCard key={crack.id} id={crack.id} imageSrc={crack.imageSrc} />
            ))}
          </div>
          
          <div className="w-full flex justify-end">
            <Navigation 
              onPrev={handlePrev} 
              onNext={handleNext} 
              showPrev={currentPage > 0}
              showNext={currentPage < totalPages - 1}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
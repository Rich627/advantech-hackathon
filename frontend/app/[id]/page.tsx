// app/[id]/page.tsx
"use client";
import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import Header from '../components/Header';
import DetailPanel from '../components/DetailPanel';
import Navigation from '../components/Navigation';
import CrackCard from '../components/CrackCard';

// Mock data
const crackDetails = {
  reportId: 'REP-2024-001',
  location: '隧道A段',
  type: 'Longitudinal',
  length: '150 公分',
  width: '2 公分',
  inspector: '張工程師',
  inspectionDate: '2024-04-25',
  treatment: '灌漿修補',
  status: '已完成'
};

const similarCracks = [
  { id: '1', imageSrc: '/images/crack1.jpg' },
  { id: '2', imageSrc: '/images/crack1.jpg' },
  { id: '3', imageSrc: '/images/crack1.jpg' },
];

// Mock multiple images of the same crack from different angles
const crackImages = [
  '/images/crack1.jpg',
  '/images/crack1.jpg',
  '/images/crack1.jpg'
];

export default function CrackDetailPage({ params }: { params: { id: string } }) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [currentSimilarPage, setCurrentSimilarPage] = useState(0);
  
  const handlePrevImage = () => {
    if (currentImageIndex > 0) {
      setCurrentImageIndex(currentImageIndex - 1);
    }
  };
  
  const handleNextImage = () => {
    if (currentImageIndex < crackImages.length - 1) {
      setCurrentImageIndex(currentImageIndex + 1);
    }
  };
  
  const handlePrevSimilar = () => {
    setCurrentSimilarPage(0); // Only two pages in this mock
  };
  
  const handleNextSimilar = () => {
    setCurrentSimilarPage(1); // Only two pages in this mock
  };

  return (
    <div>
      <Header />
      <main className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left column - crack image and details */}
          <div>
            <h2 className="text-xl font-bold mb-4">裂縫照片</h2>
            <div className="relative mb-6">
              <Image 
                src={crackImages[currentImageIndex]} 
                alt="Concrete crack" 
                width={400} 
                height={400} 
                className="border border-gray-300 w-full"
              />
              <Navigation 
                onPrev={handlePrevImage} 
                onNext={handleNextImage} 
                showPrev={currentImageIndex > 0}
                showNext={currentImageIndex < crackImages.length - 1}
                position="overlay"
              />
            </div>
            <DetailPanel details={crackDetails} />
          </div>
          
          {/* Right column - recommendations and similar cases */}
          <div>
            <h2 className="text-xl font-bold mb-4">建議處理方式</h2>
            <div className="mb-8">
              <p>報告編號: {crackDetails.reportId}</p>
              <p>位置: {crackDetails.location}</p>
              <p>裂縫類型: {crackDetails.type}</p>
              <p>裂縫長度: {crackDetails.length}</p>
            </div>
            
            <h2 className="text-xl font-bold mb-4">過往案例</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {similarCracks.map((crack) => (
                <CrackCard key={crack.id} id={crack.id} imageSrc={crack.imageSrc} />
              ))}
            </div>
            <div className="flex justify-end">
              <Navigation 
                onPrev={handlePrevSimilar} 
                onNext={handleNextSimilar} 
                showPrev={currentSimilarPage > 0}
                showNext={currentSimilarPage < 1}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
// app/components/CrackCard.tsx
"use client";
import React from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

interface CrackCardProps {
  id: string;
  imageSrc: string;
}

const CrackCard = ({ id, imageSrc }: CrackCardProps) => {
  const router = useRouter();
  
  const handleClick = () => {
    router.push(`/${id}`);
  };

  return (
    <div 
      className="border border-gray-300 rounded-md p-4 max-w-xs cursor-pointer hover:shadow-md transition-shadow"
      onClick={handleClick}
    >
      <div className="mb-4">
        <Image 
          src={imageSrc} 
          alt="Concrete crack" 
          width={200} 
          height={200} 
          className="w-full"
        />
      </div>
      <div className="text-center">
        <p className="font-medium mb-2">「雲端智生：臺灣生成式 AI 應用黑客松競賽」</p>
        <p className="text-sm mb-4">新應用與實證想法</p>
        <button className="text-blue-600 hover:underline">
          Learn more
        </button>
      </div>
    </div>
  );
};

export default CrackCard;
// app/components/Header.tsx
"use client";
import React from 'react';
import { useRouter } from 'next/navigation';

const Header = () => {
  const router = useRouter();
  
  const handleClick = () => {
    router.push('/');
  };

  return (
    <header className="bg-gray-800 text-white p-4">
      <h1 
        className="text-xl font-bold cursor-pointer hover:opacity-80 transition-opacity"
        onClick={handleClick}
      >
        檢修系統
      </h1>
    </header>
  );
};

export default Header;
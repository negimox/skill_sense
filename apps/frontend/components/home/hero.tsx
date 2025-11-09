import React from 'react';
import Link from 'next/link';
import BackgroundContainer from '@/components/common/background-container';

export default function Hero() {
  return (
    <BackgroundContainer>
      <div className="relative mb-4 w-full ">
        <h1 className="text-center text-8xl font-semibold bg-clip-text text-transparent bg-gradient-to-r from-sky-400 via-blue-400 to-violet-500">
          Skill Sense
        </h1>
      </div>
      <p className="mb-12 text-center text-lg bg-gradient-to-br from-pink-400 via-blue-400 to-violet-600 bg-clip-text text-transparent md:text-xl">
        Skills are the new currency, showcase yours.
      </p>
      <Link
        href="/resume"
        className="group relative inline-flex h-10 overflow-hidden rounded-full p-[1px]"
      >
        <span className="absolute inset-[-1000%] bg-[conic-gradient(from_90deg_at_50%_50%,#3A59D1_0%,#7AC6D2_50%,#3A59D1_100%)]" />
        <span className="inline-flex h-full w-full cursor-pointer items-center justify-center rounded-full bg-slate-950 px-3 py-1 text-sm font-medium text-gray-100 backdrop-blur-3xl">
          Get Started
          <svg
            width="16"
            height="16"
            viewBox="0 0 0.3 0.3"
            fill="#FFF"
            xmlns="http://www.w3.org/2000/svg"
            className="ml-2"
          >
            <path d="M.166.046a.02.02 0 0 1 .028 0l.09.09a.02.02 0 0 1 0 .028l-.09.09A.02.02 0 0 1 .166.226L.22.17H.03a.02.02 0 0 1 0-.04h.19L.166.074a.02.02 0 0 1 0-.028" />
          </svg>
        </span>
      </Link>
    </BackgroundContainer>
  );
}

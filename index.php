
<?php
require_once 'config.php';
?>

<!DOCTYPE html>
<html lang="en" class="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>AI Chat Assistant</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Enhanced Prism.js for advanced code syntax highlighting -->
  <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css" rel="stylesheet" id="prism-light-theme" />
  <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" id="prism-dark-theme" disabled />
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-php.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-java.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-c.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-cpp.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-css.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-markup.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-sql.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-powershell.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-typescript.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-jsx.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-tsx.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-go.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-rust.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-swift.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-kotlin.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
  <script src="notifications.js"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            primary: {
              50: '#f5f3ff',
              100: '#ede9fe',
              200: '#ddd6fe',
              300: '#c4b5fd',
              400: '#a78bfa',
              500: '#8b5cf6',
              600: '#7c3aed',
              700: '#6d28d9',
              800: '#5b21b6',
              900: '#4c1d95',
              950: '#2e1065',
            },
          }
        }
      }
    }
  </script>
  <style>
    /* Custom scrollbar */
    .scrollbar-thin::-webkit-scrollbar {
      width: 6px;
    }
    .scrollbar-thin::-webkit-scrollbar-track {
      background: transparent;
    }
    .scrollbar-thin::-webkit-scrollbar-thumb {
      background-color: #d1d5db;
      border-radius: 3px;
    }
    .dark .scrollbar-thin::-webkit-scrollbar-thumb {
      background-color: #4b5563;
    }
    
    /* Scroll buttons */
    .scroll-btn {
      position: fixed;
      right: 20px;
      width: 40px;
      height: 40px;
      background-color: rgba(139, 92, 246, 0.9);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      transition: all 0.2s ease;
      z-index: 5;  /* Changed from 50 to 5 to be below the chat input */
    }
    .scroll-btn:hover {
      transform: scale(1.1);
    }
    #scroll-top-btn {
      bottom: 160px;  /* Increased from 120px */
    }
    #scroll-bottom-btn {
      bottom: 100px;  /* Increased from 60px */
    }
    
    /* Message pre-wrap formatting */
    .message-content {
      white-space: pre-wrap;
      word-break: break-word;
    }
    
    /* Copy button animation */
    .copy-success {
      animation: fadeOut 1.5s forwards;
    }
    @keyframes fadeOut {
      0% { opacity: 1; }
      70% { opacity: 1; }
      100% { opacity: 0; }
    }

    /* Enhanced code block styling */
    .code-block-container {
      background: #1f2937;
      border-radius: 0.5rem;
      overflow: hidden;
      margin: 0.75rem 0;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .code-header {
      background: #374151;
      padding: 0.5rem 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #4b5563;
    }

    .code-language {
      color: #d1d5db;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .code-copy-btn {
      background: #4b5563;
      color: #d1d5db;
      border: none;
      padding: 0.25rem 0.5rem;
      border-radius: 0.25rem;
      font-size: 0.75rem;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .code-copy-btn:hover {
      background: #6b7280;
    }

    .code-copy-btn.copied {
      background: #059669;
      color: white;
    }

    /* Better code styling */
    pre[class*="language-"] {
      margin: 0 !important;
      padding: 1rem !important;
      background: #1f2937 !important;
      font-size: 0.875rem !important;
      line-height: 1.5 !important;
      overflow-x: auto !important;
    }

    code[class*="language-"] {
      color: #f9fafb !important;
      font-family: 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace !important;
    }

    /* Enhanced Code Block Styling for Light and Dark Modes */
    .code-block {
      background: #1e293b !important;
      border: 1px solid #334155 !important;
      border-radius: 12px !important;
      overflow: hidden;
      margin: 16px 0 !important;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }

    .dark .code-block {
      background: #0f172a !important;
      border-color: #1e293b !important;
      box-shadow: 0 4px 6px -1px rgba(255, 255, 255, 0.05), 0 2px 4px -1px rgba(255, 255, 255, 0.03) !important;
    }

    .code-header {
      background: #334155 !important;
      padding: 8px 16px !important;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      font-weight: 500;
      color: #e2e8f0 !important;
      border-bottom: 1px solid #475569 !important;
    }

    .dark .code-header {
      background: #1e293b !important;
      border-bottom-color: #334155 !important;
    }

    .language-label {
      color: #a3a3a3 !important;
      font-family: 'SF Mono', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .copy-button {
      background: #475569 !important;
      color: #e2e8f0 !important;
      border: none;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.2s;
      font-family: 'SF Mono', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
    }

    .copy-button:hover {
      background: #64748b !important;
      transform: translateY(-1px);
    }

    .dark .copy-button {
      background: #334155 !important;
    }

    .dark .copy-button:hover {
      background: #475569 !important;
    }

    /* Enhanced Prism Token Styling for Better Readability */
    pre[class*="language-"] {
      background: transparent !important;
      padding: 16px !important;
      margin: 0 !important;
      border-radius: 0 !important;
      font-family: 'SF Mono', Consolas, 'Liberation Mono', Menlo, Courier, monospace !important;
      font-size: 14px !important;
      line-height: 1.6 !important;
      overflow-x: auto;
    }

    code[class*="language-"] {
      background: transparent !important;
      font-family: 'SF Mono', Consolas, 'Liberation Mono', Menlo, Courier, monospace !important;
      font-size: 14px !important;
      line-height: 1.6 !important;
    }

    /* Dark Mode Token Colors */
    .token.comment, .token.prolog, .token.doctype, .token.cdata { 
      color: #64748b !important; 
      font-style: italic;
    }
    
    .token.string, .token.attr-value { 
      color: #22c55e !important; 
    }
    
    .token.number { 
      color: #f59e0b !important; 
      font-weight: 500;
    }
    
    .token.keyword, .token.important { 
      color: #8b5cf6 !important; 
      font-weight: 600 !important; 
    }
    
    .token.function, .token.class-name { 
      color: #3b82f6 !important; 
      font-weight: 500;
    }
    
    .token.operator, .token.entity, .token.url { 
      color: #ef4444 !important; 
    }
    
    .token.punctuation { 
      color: #94a3b8 !important; 
    }
    
    .token.variable { 
      color: #f59e0b !important; 
    }
    
    .token.property, .token.tag { 
      color: #ec4899 !important; 
      font-weight: 500;
    }
    
    .token.boolean, .token.constant { 
      color: #06b6d4 !important; 
      font-weight: 500;
    }
    
    .token.selector, .token.attr-name { 
      color: #a78bfa !important; 
    }
    
    .token.regex, .token.important { 
      color: #fbbf24 !important; 
    }
    
    .token.atrule { 
      color: #10b981 !important; 
    }

    .token.builtin, .token.symbol { 
      color: #06b6d4 !important; 
    }

    /* Light Mode Overrides */
    html:not(.dark) .code-block {
      background: #f1f5f9 !important;
      border-color: #cbd5e1 !important;
      box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
    }

    html:not(.dark) .code-header {
      background: #e2e8f0 !important;
      color: #475569 !important;
      border-bottom-color: #cbd5e1 !important;
    }

    html:not(.dark) .language-label {
      color: #64748b !important;
    }

    html:not(.dark) .copy-button {
      background: #cbd5e1 !important;
      color: #475569 !important;
    }

    html:not(.dark) .copy-button:hover {
      background: #94a3b8 !important;
    }

    html:not(.dark) pre[class*="language-"] {
      background: #f8fafc !important;
      color: #1e293b !important;
      border: 1px solid #e2e8f0 !important;
    }

    html:not(.dark) code[class*="language-"] {
      background: transparent !important;
      color: #1e293b !important;
    }

    /* Light Mode Token Colors */
    html:not(.dark) .token.comment, 
    html:not(.dark) .token.prolog, 
    html:not(.dark) .token.doctype, 
    html:not(.dark) .token.cdata { 
      color: #64748b !important; 
    }
    
    html:not(.dark) .token.string, 
    html:not(.dark) .token.attr-value { 
      color: #059669 !important; 
    }
    
    html:not(.dark) .token.number { 
      color: #d97706 !important; 
    }
    
    html:not(.dark) .token.keyword, 
    html:not(.dark) .token.important { 
      color: #7c3aed !important; 
    }
    
    html:not(.dark) .token.function, 
    html:not(.dark) .token.class-name { 
      color: #2563eb !important; 
    }
    
    html:not(.dark) .token.operator, 
    html:not(.dark) .token.entity, 
    html:not(.dark) .token.url { 
      color: #dc2626 !important; 
    }
    
    html:not(.dark) .token.punctuation { 
      color: #475569 !important; 
    }
    
    html:not(.dark) .token.variable { 
      color: #d97706 !important; 
    }
    
    html:not(.dark) .token.property, 
    html:not(.dark) .token.tag { 
      color: #be185d !important; 
    }
    
    html:not(.dark) .token.boolean, 
    html:not(.dark) .token.constant { 
      color: #0891b2 !important; 
    }
    
    /* Mic animation */
    .mic-active {
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.1); }
      100% { transform: scale(1); }
    }
  </style>
</head>
<body class="bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-white transition-colors duration-200">
  <div class="flex flex-col h-screen">
    <!-- Header -->
    <header class="sticky top-0 z-10 backdrop-blur-md bg-white/70 dark:bg-gray-800/70 border-b border-gray-200 dark:border-gray-700 shadow-sm">
      <div class="container mx-auto px-4 py-3 flex justify-between items-center">
        <div class="flex items-center space-x-2">
          <div class="h-8 w-8 rounded-full bg-gradient-to-r from-primary-500 to-primary-700 flex items-center justify-center text-white font-bold">
            AI
          </div>
          <span class="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">Gemini 1.5 Flash</span>
          <h1 class="text-xl font-semibold text-gray-800 dark:text-white">AI Chat Assistant</h1>
        </div>

        <div class="flex items-center space-x-3">
          <!-- LaTeX Editor Button -->
          <button
            onclick="window.open('latex-editor/', '_blank')"
            class="flex items-center space-x-2 px-3 py-2 bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700 text-white rounded-lg transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl"
            aria-label="LaTeX Editor"
            title="Professional LaTeX to PDF Editor"
          >
            <svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span class="text-sm font-medium">LaTeX</span>
          </button>

          <!-- Conversation History Button -->
          <button
            id="open-sidebar"
            class="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200"
            aria-label="Conversation history"
          >
            <svg class="h-5 w-5 text-gray-600 dark:text-gray-200" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" />
            </svg>
          </button>

          <!-- Search Button -->
          <button
            id="search-toggle"
            class="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200"
            aria-label="Search conversations"
          >
            <svg class="h-5 w-5 text-gray-600 dark:text-gray-200" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>

          <button
            id="theme-toggle"
            class="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200"
            aria-label="Toggle dark mode"
          >
            <svg id="sun-icon" class="h-5 w-5 text-gray-600 hidden dark:block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg id="moon-icon" class="h-5 w-5 text-gray-600 block dark:hidden" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>

          <!-- Language Selector -->
          <div class="relative group">
            <button
              id="language-toggle"
              class="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200"
              aria-label="Language"
            >
              <svg class="h-5 w-5 text-gray-600 dark:text-gray-200" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
              </svg>
            </button>

            <div id="language-menu" class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-20 border border-gray-200 dark:border-gray-700">
              <div class="py-1">
                <button class="language-option block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700" data-lang="en">
                  🇺🇸 English
                </button>
                <button class="language-option block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700" data-lang="es">
                  🇪🇸 Español
                </button>
                <button class="language-option block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700" data-lang="fr">
                  🇫🇷 Français
                </button>
                <button class="language-option block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700" data-lang="de">
                  🇩🇪 Deutsch
                </button>
                <button class="language-option block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700" data-lang="hi">
                  🇮🇳 हिंदी
                </button>
                <button class="language-option block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700" data-lang="zh">
                  🇨🇳 中文
                </button>
                <button class="language-option block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700" data-lang="ja">
                  🇯🇵 日本語
                </button>
              </div>
            </div>
          </div>

          <div class="relative group">
            <button
              class="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200"
              aria-label="Settings"
            >
              <svg class="h-5 w-5 text-gray-600 dark:text-gray-200" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>

            <div class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-20 border border-gray-200 dark:border-gray-700">
              <div class="py-1">
                <button
                  id="clear-chat"
                  class="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Clear Chat History
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Chat Container -->
    <div id="chat-container" class="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
      <div id="welcome-message" class="flex flex-col items-center justify-center h-full text-center">
        <div class="w-16 h-16 mb-4 rounded-full bg-gradient-to-r from-primary-500 to-primary-700 flex items-center justify-center">
          <span class="text-white text-2xl">AI</span>
        </div>
        <h2 class="text-xl font-semibold text-gray-700 dark:text-gray-200 mb-2">
          Welcome to AI Chat Assistant
        </h2>
        <div class="mb-2">
          <span class="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">Powered by Gemini 1.5 Flash</span>
        </div>
        <p class="text-gray-500 dark:text-gray-400 max-w-md">
          Start a conversation by typing a message below. Your chat history will be saved locally.
        </p>
        <!-- Enhanced Pro Tips Section -->
        <div class="mt-6 max-w-2xl">
          <div class="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-xl p-6 border border-primary-100 dark:border-primary-800">
            <div class="flex items-center mb-4">
              <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-gradient-to-r from-primary-500 to-blue-500 rounded-full flex items-center justify-center">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                  </svg>
                </div>
              </div>
              <div class="ml-3">
                <h3 class="text-lg font-semibold text-gray-800 dark:text-white">✨ What I Can Do</h3>
                <p class="text-sm text-gray-600 dark:text-gray-300">Explore my powerful capabilities</p>
              </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <!-- Image Generation -->
              <div class="flex items-start p-3 bg-white/50 dark:bg-gray-800/50 rounded-lg border border-white/20 dark:border-gray-700/50 hover:shadow-md transition-all duration-200 group cursor-pointer" onclick="setQuickPrompt('Create an image of a sunset over mountains')">
                <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-pink-400 to-red-500 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                  </svg>
                </div>
                <div class="ml-3 flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">Generate Images</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">"Create a sunset over mountains"</p>
                </div>
              </div>

              <!-- Image Analysis -->
              <div class="flex items-start p-3 bg-white/50 dark:bg-gray-800/50 rounded-lg border border-white/20 dark:border-gray-700/50 hover:shadow-md transition-all duration-200 group cursor-pointer" onclick="setQuickPrompt('What is in this picture?')">
                <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-400 to-indigo-500 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                  </svg>
                </div>
                <div class="ml-3 flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">Analyze Images</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">"What's in this picture?"</p>
                </div>
              </div>

              <!-- Code Writing -->
              <div class="flex items-start p-3 bg-white/50 dark:bg-gray-800/50 rounded-lg border border-white/20 dark:border-gray-700/50 hover:shadow-md transition-all duration-200 group cursor-pointer" onclick="setQuickPrompt('Write a Python function to sort a list')">
                <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-green-400 to-emerald-500 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path>
                  </svg>
                </div>
                <div class="ml-3 flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">Write Code</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">"Python function to sort a list"</p>
                </div>
              </div>

              <!-- Translation -->
              <div class="flex items-start p-3 bg-white/50 dark:bg-gray-800/50 rounded-lg border border-white/20 dark:border-gray-700/50 hover:shadow-md transition-all duration-200 group cursor-pointer" onclick="setQuickPrompt('Translate Hello world to Hindi')">
                <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-400 to-cyan-500 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"></path>
                  </svg>
                </div>
                <div class="ml-3 flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">Translate Text</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">"Hello world to Hindi"</p>
                </div>
              </div>

              <!-- Summarization -->
              <div class="flex items-start p-3 bg-white/50 dark:bg-gray-800/50 rounded-lg border border-white/20 dark:border-gray-700/50 hover:shadow-md transition-all duration-200 group cursor-pointer" onclick="setQuickPrompt('Summarize this content for me')">
                <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-orange-400 to-red-500 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                  </svg>
                </div>
                <div class="ml-3 flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">Summarize Content</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">"Summarize this paragraph"</p>
                </div>
              </div>

              <!-- Creative Writing -->
              <div class="flex items-start p-3 bg-white/50 dark:bg-gray-800/50 rounded-lg border border-white/20 dark:border-gray-700/50 hover:shadow-md transition-all duration-200 group cursor-pointer" onclick="setQuickPrompt('Write a short story about space exploration')">
                <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-teal-400 to-blue-500 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
                  </svg>
                </div>
                <div class="ml-3 flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">Creative Writing</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">"Write a story about space"</p>
                </div>
              </div>

              <!-- Brainstorming -->
              <div class="flex items-start p-3 bg-white/50 dark:bg-gray-800/50 rounded-lg border border-white/20 dark:border-gray-700/50 hover:shadow-md transition-all duration-200 group cursor-pointer" onclick="setQuickPrompt('Give me 5 startup ideas for eco-friendly products')">
                <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                  </svg>
                </div>
                <div class="ml-3 flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">Brainstorm Ideas</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">"5 eco-friendly startup ideas"</p>
                </div>
              </div>

              <!-- Q&A with Reasoning -->
              <div class="flex items-start p-3 bg-white/50 dark:bg-gray-800/50 rounded-lg border border-white/20 dark:border-gray-700/50 hover:shadow-md transition-all duration-200 group cursor-pointer" onclick="setQuickPrompt('Explain quantum computing in simple terms')">
                <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
                <div class="ml-3 flex-1">
                  <h4 class="text-sm font-medium text-gray-800 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">Q&A with Reasoning</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">"Explain quantum computing"</p>
                </div>
              </div>
            </div>

            <div class="mt-4 text-center">
              <p class="text-xs text-gray-500 dark:text-gray-400"> Click any card above to get started, or type your own question!</p>
            </div>
          </div>
        </div>
      </div>

      <div id="messages-container" class="hidden space-y-4">
        <!-- Messages will be dynamically inserted here -->
      </div>

      <!-- Enhanced Loading/Typing Indicator -->
      <div id="loading-indicator" class="hidden flex justify-start">
        <div class="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-md dark:shadow-gray-700/20 rounded-tl-none max-w-xs">
          <div class="flex items-center space-x-3">
            <div class="flex space-x-1">
              <div class="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>
            <span id="typing-text" class="text-gray-600 dark:text-gray-300 text-sm">AI is thinking...</span>
          </div>
          <div id="typing-progress" class="hidden mt-2">
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
              <div class="bg-primary-500 h-1 rounded-full transition-all duration-300" style="width: 0%"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Replies -->
    <div id="quick-replies" class="sticky bottom-20 z-5 px-4 py-2 overflow-x-auto whitespace-nowrap scrollbar-thin">
      <div class="inline-flex space-x-2">
        <button class="quick-reply-btn px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
          Tell me a joke
        </button>
        <button class="quick-reply-btn px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
          Explain quantum computing
        </button>
        <button class="quick-reply-btn px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
          Write a poem about nature
        </button>
        <button class="quick-reply-btn px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
          Help me with JavaScript
        </button>
        <button class="quick-reply-btn px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
          Recommend a book
        </button>
        <button class="quick-reply-btn px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
          Create a workout plan
        </button>
        <button class="quick-reply-btn px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
          Generate an image
        </button>
      </div>
    </div>

    <!-- Chat Input -->
    <div class="sticky bottom-0 z-10 backdrop-blur-md bg-white/70 dark:bg-gray-800/70 border-t border-gray-200 dark:border-gray-700 p-4">
      <form id="chat-form" class="container mx-auto" enctype="multipart/form-data">
        <div class="relative flex items-center">
          <div class="absolute inset-0 -z-10 rounded-full bg-white dark:bg-gray-700/50 shadow-lg backdrop-blur-sm border border-gray-200 dark:border-gray-700"></div>

          <button
            type="button"
            id="mic-button"
            class="p-3 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:opacity-80 transition-colors duration-200 ml-1"
            aria-label="Start voice input"
          >
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </button>
          
          <!-- Image Upload Button -->
          <label for="image-upload" class="p-3 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:opacity-80 transition-colors duration-200 ml-1 cursor-pointer">
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </label>
          <input 
            type="file" 
            id="image-upload" 
            name="image" 
            accept="image/jpeg,image/png,image/gif,image/webp" 
            class="hidden" 
          />
          
          <!-- Selected Image Preview -->
          <div id="image-preview-container" class="hidden absolute bottom-full left-0 mb-2 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
            <div class="flex items-center">
              <img id="image-preview" class="h-16 w-auto rounded" alt="Selected image" />
              <button type="button" id="remove-image" class="ml-2 text-gray-500 hover:text-red-500">
                <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <input
            type="text"
            id="prompt-input"
            placeholder="Type your message..."
            class="flex-1 bg-transparent border-0 focus:ring-0 text-gray-800 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 px-4 py-3"
          />



          <button
            type="submit"
            id="send-button"
            class="p-3 rounded-full bg-gradient-to-r from-primary-500 to-primary-700 text-white hover:opacity-90 transition-colors duration-200 mr-1 ml-2 disabled:opacity-50 disabled:cursor-not-allowed"  /* Added ml-2 for left margin */
            aria-label="Send message"
          >
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>

    <!-- Toast Notification -->
    <div id="toast" class="fixed bottom-24 left-1/2 transform -translate-x-1/2 z-50 hidden">
      <div class="px-4 py-3 rounded-lg shadow-lg flex items-center space-x-2 bg-green-500 text-white">
        <span id="toast-message">Message sent successfully!</span>
        <button id="close-toast" class="text-white hover:text-gray-200">
          <svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- Conversation History Sidebar -->
    <div id="conversation-sidebar" class="fixed inset-y-0 left-0 w-80 bg-white dark:bg-gray-800 shadow-lg transform -translate-x-full transition-transform duration-300 ease-in-out z-30">
      <div class="h-full flex flex-col">
        <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <h2 class="text-lg font-semibold">Conversations</h2>
          <button id="close-sidebar" class="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-4 space-y-2">
          <button id="new-chat-btn" class="w-full flex items-center p-3 rounded-md bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 hover:bg-primary-200 dark:hover:bg-primary-800 transition-colors">
            <svg class="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New Chat
          </button>
          
          <div class="border-t border-gray-200 dark:border-gray-700 my-2 pt-2">
            <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Recent Conversations</h3>
            <div id="conversation-list" class="space-y-1">
              <!-- Conversation items will be dynamically inserted here -->
            </div>
          </div>
        </div>
        
        <div class="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
          <button id="save-conversation" class="w-full px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-md text-sm flex items-center justify-center space-x-2">
            <svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
            </svg>
            <span>Save Current Chat</span>
          </button>
          <button id="export-chat-btn" class="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md text-sm flex items-center justify-center space-x-2">
            <svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span>Export Chat</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Export Modal -->
    <div id="export-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 hidden">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md">
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Export Chat</h3>
            <button id="close-export-modal" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <!-- Chat Selection -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Select Chat to Export:</label>
            <select id="chat-selection" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="current">Current Chat</option>
              <!-- Saved conversations will be added here dynamically -->
            </select>
          </div>
          
          <!-- Format Selection -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Export Format:</label>
            <div class="space-y-2">
              <label class="flex items-center">
                <input type="radio" name="export-format" value="txt" checked class="mr-2">
                <span>Text File (.txt)</span>
              </label>
              <label class="flex items-center">
                <input type="radio" name="export-format" value="pdf" class="mr-2">
                <span>PDF Document (.pdf)</span>
              </label>
              <label class="flex items-center">
                <input type="radio" name="export-format" value="html" class="mr-2">
                <span>HTML Page (.html)</span>
              </label>
            </div>
          </div>
          
          <!-- Export Button -->
          <div class="flex space-x-3">
            <button id="cancel-export" class="flex-1 px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Cancel</button>
            <button id="confirm-export" class="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">Export</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Search Modal -->
    <div id="search-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 hidden">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-96">
        <div class="p-4 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center space-x-2">
            <svg class="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input 
              id="search-input" 
              type="text" 
              placeholder="Search through your conversations..." 
              class="flex-1 bg-transparent border-0 focus:ring-0 text-gray-800 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
            />
            <button id="close-search" class="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
              <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <div class="p-4 max-h-80 overflow-y-auto">
          <div id="search-results" class="space-y-2">
            <div class="text-center text-gray-500 dark:text-gray-400">
              Type to search through your conversation history...
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Scroll Buttons -->
    <button id="scroll-top-btn" class="scroll-btn" aria-label="Scroll to top">
      <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
    </button>
    <button id="scroll-bottom-btn" class="scroll-btn" aria-label="Scroll to bottom">
      <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
      </svg>
    </button>
  </div>

  <script>
    // Global error handler for unhandled JavaScript errors
    window.addEventListener('error', (event) => {
      console.error('Global JavaScript error:', event.error);
      console.error('Error details:', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack
      });

      // Don't show toast for every error to avoid spam
      if (event.error && event.error.message && !event.error.message.includes('Script error')) {
        // Only show user-friendly errors
        if (event.error.message.includes('tokenizePlaceholders') ||
            event.error.message.includes('Prism') ||
            event.error.message.includes('EventSource')) {
          console.warn('Known issue detected, handled gracefully');
        }
      }
    });

    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled promise rejection:', event.reason);

      // Prevent the default browser behavior
      event.preventDefault();

      // Handle specific promise rejections
      if (event.reason && typeof event.reason === 'object') {
        if (event.reason.message && event.reason.message.includes('fetch')) {
          console.warn('Network error handled gracefully');
        }
      }
    });

    // DOM Elements
    const chatForm = document.getElementById('chat-form');
    const promptInput = document.getElementById('prompt-input');
    const sendButton = document.getElementById('send-button');
    const micButton = document.getElementById('mic-button');
    const messagesContainer = document.getElementById('messages-container');
    const welcomeMessage = document.getElementById('welcome-message');
    const loadingIndicator = document.getElementById('loading-indicator');
    const typingText = document.getElementById('typing-text');
    const typingProgress = document.getElementById('typing-progress');
    // charCount removed - unlimited input length
    const themeToggle = document.getElementById('theme-toggle');
    const clearChatButton = document.getElementById('clear-chat');
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    const closeToast = document.getElementById('close-toast');
    const chatContainer = document.getElementById('chat-container');
    const scrollTopBtn = document.getElementById('scroll-top-btn');
    const scrollBottomBtn = document.getElementById('scroll-bottom-btn');

    // New UI Elements
    const conversationSidebar = document.getElementById('conversation-sidebar');
    const openSidebarBtn = document.getElementById('open-sidebar');
    const closeSidebarBtn = document.getElementById('close-sidebar');
    const newChatBtn = document.getElementById('new-chat-btn');
    const saveConversationBtn = document.getElementById('save-conversation');
    const exportAllChatsBtn = document.getElementById('export-all-chats');
    const searchToggle = document.getElementById('search-toggle');
    const searchModal = document.getElementById('search-modal');
    const searchInput = document.getElementById('search-input');
    const closeSearchBtn = document.getElementById('close-search');
    const searchResults = document.getElementById('search-results');
    const conversationList = document.getElementById('conversation-list');
    const quickReplyButtons = document.querySelectorAll('.quick-reply-btn');

    // State
    let messages = [];
    let isListening = false;
    let conversationBranches = JSON.parse(localStorage.getItem('conversationBranches') || '[]');
    let currentConversationId = null;

    // Load messages from localStorage with error handling
    function loadMessages() {
      try {
        const savedMessages = localStorage.getItem('chatMessages');
        if (savedMessages) {
          const parsedMessages = JSON.parse(savedMessages);
          if (Array.isArray(parsedMessages)) {
            messages = parsedMessages;
            if (messages.length > 0) {
              welcomeMessage.classList.add('hidden');
              messagesContainer.classList.remove('hidden');
              renderMessages();
            }
          } else {
            console.warn('Invalid messages format in localStorage, clearing...');
            localStorage.removeItem('chatMessages');
          }
        }
      } catch (error) {
        console.error('Error loading messages from localStorage:', error);
        localStorage.removeItem('chatMessages');
        messages = [];
      }
    }

    // Save messages to localStorage with error handling
    function saveMessages() {
      try {
        localStorage.setItem('chatMessages', JSON.stringify(messages));
      } catch (error) {
        console.error('Error saving messages to localStorage:', error);
        showToast('Failed to save chat history', 'error');
      }
    }

    // Render messages
    function renderMessages() {
      messagesContainer.innerHTML = '';
      
      messages.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} msg ${message.role}`;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `max-w-[80%] md:max-w-[70%] p-3 rounded-2xl ${
          message.role === 'user'
            ? 'bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-tr-none'
            : 'bg-white dark:bg-gray-800 shadow-md dark:shadow-gray-700/20 text-gray-800 dark:text-gray-200 rounded-tl-none'
        }`;
        
        // Add image if present
        if (message.hasImage && message.imageData) {
          const imageContainer = document.createElement('div');
          imageContainer.className = 'mb-2';
          
          const img = document.createElement('img');
          img.src = message.imageData;
          img.className = 'rounded-lg max-w-full max-h-48 object-contain';
          img.alt = 'Uploaded image';
          
          imageContainer.appendChild(img);
          bubbleDiv.appendChild(imageContainer);
        }
        
        // Create message content with pre-wrap formatting and code highlighting
        const contentP = document.createElement('div');
        contentP.className = 'text-sm md:text-base message-content';
        
        // Process content for code blocks
        const content = message.content;
        
        // Check if content contains code blocks
        if (content.includes('```')) {
          // Split by code blocks
          const parts = content.split(/```(\w*)\n?/);
          let isCodeBlock = false;
          let language = '';
          
          for (let i = 0; i < parts.length; i++) {
            if (i % 2 === 0) {
              // Regular text
              if (parts[i].trim()) {
                const textNode = document.createElement('p');
                textNode.textContent = parts[i];
                contentP.appendChild(textNode);
              }
            } else {
              // This is a language identifier
              language = parts[i] || 'javascript'; // Default to javascript if no language specified
              isCodeBlock = true;
              
              // The next part is the code block content
              if (i + 1 < parts.length) {
                const code = parts[i + 1].trim();
                const preElement = document.createElement('pre');
                preElement.className = `language-${language} rounded my-2`;
                
                const codeElement = document.createElement('code');
                codeElement.className = `language-${language}`;
                codeElement.textContent = code;
                
                preElement.appendChild(codeElement);
                contentP.appendChild(preElement);
                
                // Skip the next part as we've already processed it
                i++;
              }
            }
          }
          
          // Apply syntax highlighting with error handling
          setTimeout(() => {
            applySyntaxHighlighting(contentP);
          }, 0);
        } else {
          // No code blocks, just set the text content
          contentP.textContent = content;
        }
        
        // Create timestamp
        const timeDiv = document.createElement('div');
        timeDiv.className = `text-xs mt-1 ${
          message.role === 'user' ? 'text-primary-200' : 'text-gray-500 dark:text-gray-400'
        }`;
        timeDiv.textContent = new Date(message.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit'
        });
        
        // Add copy button and reactions for assistant messages
        if (message.role === 'assistant') {
          const actionsDiv = document.createElement('div');
          actionsDiv.className = 'flex justify-between items-center mt-2';
          
          // Message Reactions
          const reactionsDiv = document.createElement('div');
          reactionsDiv.className = 'flex space-x-1';
          
          const reactions = ['👍', '👎', '❤️', '😂', '😮'];
          reactions.forEach(emoji => {
            const reactionBtn = document.createElement('button');
            reactionBtn.className = 'reaction-btn p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full text-sm transition-colors';
            reactionBtn.setAttribute('data-emoji', emoji);
            reactionBtn.textContent = emoji;
            reactionBtn.onclick = function() {
              this.classList.toggle('bg-primary-100');
              this.classList.toggle('dark:bg-primary-900');
              showToast(`Reaction ${emoji} recorded`, 'success');
            };
            reactionsDiv.appendChild(reactionBtn);
          });
          
          // Copy button
          const copyButton = document.createElement('button');
          copyButton.className = 'text-gray-500 dark:text-gray-400 hover:text-primary-500 dark:hover:text-primary-400 focus:outline-none p-1 rounded-full';
          copyButton.innerHTML = '📋';
          copyButton.setAttribute('aria-label', 'Copy message');
          copyButton.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            copyToClipboard(message.content, this);
          };
          
          actionsDiv.appendChild(reactionsDiv);
          actionsDiv.appendChild(copyButton);
          bubbleDiv.appendChild(contentP);
          bubbleDiv.appendChild(timeDiv);
          bubbleDiv.appendChild(actionsDiv);
        } else {
          // Add copy button for user messages too
          const actionsDiv = document.createElement('div');
          actionsDiv.className = 'flex justify-end items-center mt-2';

          const copyButton = document.createElement('button');
          copyButton.className = 'text-gray-500 dark:text-gray-400 hover:text-primary-500 dark:hover:text-primary-400 focus:outline-none p-1 rounded-full';
          copyButton.innerHTML = '📋';
          copyButton.setAttribute('aria-label', 'Copy message');
          copyButton.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            copyToClipboard(message.content, this);
          };

          actionsDiv.appendChild(copyButton);
          bubbleDiv.appendChild(contentP);
          bubbleDiv.appendChild(timeDiv);
          bubbleDiv.appendChild(actionsDiv);
        }
        
        messageDiv.appendChild(bubbleDiv);
        messagesContainer.appendChild(messageDiv);
      });
      
      // Scroll to bottom after rendering messages
      chatContainer.scrollTop = chatContainer.scrollHeight;
      
      // Show/hide scroll buttons based on content
      updateScrollButtonsVisibility();
    }

    // Add a message
    function addMessage(content, role, imageData = null) {
      const message = {
        id: Date.now().toString(),
        content,
        role,
        timestamp: new Date(),
        hasImage: !!imageData,
        imageData: imageData
      };
      
      // If this is a user message with an image, save the image data
      if (role === 'user' && selectedImage) {
        const reader = new FileReader();
        reader.onload = (e) => {
          message.hasImage = true;
          message.imageData = e.target.result;
          // Update the message in the array
          const index = messages.findIndex(m => m.id === message.id);
          if (index !== -1) {
            messages[index] = message;
            saveMessages();
            renderMessages();
          }
        };
        reader.readAsDataURL(selectedImage);
      }
      
      messages.push(message);
      saveMessages();
      
      if (messages.length === 1) {
        welcomeMessage.classList.add('hidden');
        messagesContainer.classList.remove('hidden');
      }
      
      renderMessages();
    }

    // Helper function to get display name for programming languages
    function getLanguageDisplayName(lang) {
      const languageNames = {
        'javascript': 'JavaScript',
        'js': 'JavaScript',
        'typescript': 'TypeScript',
        'ts': 'TypeScript',
        'python': 'Python',
        'py': 'Python',
        'php': 'PHP',
        'java': 'Java',
        'cpp': 'C++',
        'c': 'C',
        'csharp': 'C#',
        'cs': 'C#',
        'css': 'CSS',
        'html': 'HTML',
        'xml': 'XML',
        'json': 'JSON',
        'sql': 'SQL',
        'bash': 'Bash',
        'shell': 'Shell',
        'powershell': 'PowerShell',
        'rust': 'Rust',
        'go': 'Go',
        'swift': 'Swift',
        'kotlin': 'Kotlin',
        'jsx': 'JSX',
        'tsx': 'TSX',
        'yaml': 'YAML',
        'yml': 'YAML',
        'markdown': 'Markdown',
        'md': 'Markdown'
      };
      return languageNames[lang.toLowerCase()] || lang.toUpperCase();
    }

    // Enhanced copy to clipboard function with visual feedback
    function copyCodeToClipboard(code, button) {
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(code).then(() => {
          showCopySuccess(button);
        }).catch(() => {
          fallbackCopyToClipboard(code, button);
        });
      } else {
        fallbackCopyToClipboard(code, button);
      }
    }

    function fallbackCopyToClipboard(code, button) {
      const textArea = document.createElement('textarea');
      textArea.value = code;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      try {
        const successful = document.execCommand('copy');
        if (successful) {
          showCopySuccess(button);
        } else {
          showCopyError(button);
        }
      } catch (err) {
        showCopyError(button);
      }
      
      document.body.removeChild(textArea);
    }

    function showCopySuccess(button) {
      const originalText = button.innerHTML;
      button.innerHTML = '✅ Copied!';
      button.style.background = '#10b981';
      setTimeout(() => {
        button.innerHTML = originalText;
        button.style.background = '';
      }, 2000);
    }

    function showCopyError(button) {
      const originalText = button.innerHTML;
      button.innerHTML = ' !! Failed';
      button.style.background = '#ef4444';
      setTimeout(() => {
        button.innerHTML = originalText;
        button.style.background = '';
      }, 2000);
    }

    // Enhanced process code blocks with better styling and copy buttons
    function processCodeBlocks(text, container) {
      // Clear the container
      container.innerHTML = '';

      // Check if content contains code blocks
      if (text.includes('```')) {
        // Split by code blocks
        const parts = text.split(/```(\w*)\n?/);

        for (let i = 0; i < parts.length; i++) {
          if (i % 2 === 0) {
            // Regular text
            if (parts[i].trim()) {
              const textNode = document.createElement('div');
              textNode.className = 'mb-2';
              textNode.textContent = parts[i];
              container.appendChild(textNode);
            }
          } else {
            // This is a language identifier
            const language = parts[i] || 'javascript';

            // The next part is the code block content
            if (i + 1 < parts.length) {
              const code = parts[i + 1].trim();

              // Create code block container with enhanced styling
              const codeContainer = document.createElement('div');
              codeContainer.className = 'code-block';

              // Create header with language and copy button
              const header = document.createElement('div');
              header.className = 'code-header';

              const languageLabel = document.createElement('span');
              languageLabel.className = 'language-label';
              languageLabel.textContent = getLanguageDisplayName(language);

              const copyBtn = document.createElement('button');
              copyBtn.className = 'copy-button';
              copyBtn.innerHTML = '📋 Copy';
              copyBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                copyCodeToClipboard(code, this);
              };

              header.appendChild(languageLabel);
              header.appendChild(copyBtn);

              // Create pre element for code
              const preElement = document.createElement('pre');
              preElement.className = `language-${language}`;

              const codeElement = document.createElement('code');
              codeElement.className = `language-${language}`;
              codeElement.textContent = code;

              preElement.appendChild(codeElement);

              // Assemble code block
              codeContainer.appendChild(header);
              codeContainer.appendChild(preElement);
              container.appendChild(codeContainer);

              // Apply syntax highlighting immediately
              applySyntaxHighlighting(preElement);

              // Skip the next part as we've already processed it
              i++;
            }
          }
        }
      } else {
        // No code blocks, just set the text content
        container.textContent = text;
      }
      
      // Update the messages array with the final content
      const lastMessage = messages[messages.length - 1];
      if (lastMessage && lastMessage.role === 'assistant') {
        lastMessage.content = text;
        saveMessages();
      }
    }

    // Enhanced syntax highlighting function with immediate processing
    function applySyntaxHighlighting(container) {
      if (typeof Prism === 'undefined') {
        console.warn('Prism.js is not available for syntax highlighting');
        applyBasicCodeStyling(container);
        return;
      }

      try {
        // Find code elements in the container
        const codeElements = container.querySelectorAll('code[class*="language-"]');

        codeElements.forEach(codeElement => {
          // Apply highlighting immediately without delay
          if (typeof Prism.highlightElement === 'function') {
            Prism.highlightElement(codeElement);
          } else if (typeof Prism.highlightAllUnder === 'function') {
            Prism.highlightAllUnder(container);
          } else {
            console.warn('Prism highlighting methods not available');
            applyBasicCodeStyling(container);
          }
        });

      } catch (error) {
        console.error('Prism.js syntax highlighting error:', error);
        applyBasicCodeStyling(container);
      }
    }

    // Fallback basic code styling
    function applyBasicCodeStyling(container) {
      const codeElements = container.querySelectorAll('code');
      codeElements.forEach(codeEl => {
        codeEl.style.backgroundColor = '#1f2937';
        codeEl.style.color = '#f9fafb';
        codeEl.style.padding = '1rem';
        codeEl.style.borderRadius = '0.375rem';
        codeEl.style.fontFamily = 'Monaco, Consolas, "Liberation Mono", "Courier New", monospace';
        codeEl.style.fontSize = '0.875rem';
        codeEl.style.lineHeight = '1.5';
        codeEl.style.display = 'block';
        codeEl.style.overflowX = 'auto';
      });
    }

    // Enhanced copy function specifically for code blocks
    function copyCodeToClipboard(code, buttonElement) {
      copyToClipboard(code, buttonElement);

      // Update button text temporarily
      const originalHTML = buttonElement.innerHTML;
      buttonElement.innerHTML = '<span>✅</span><span>Copied!</span>';
      buttonElement.classList.add('bg-green-600');

      setTimeout(() => {
        buttonElement.innerHTML = originalHTML;
        buttonElement.classList.remove('bg-green-600');
      }, 2000);
    }

    // Enhanced copy to clipboard function with fallback
    function copyToClipboard(text, buttonElement) {
      // Try modern clipboard API first
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text)
          .then(() => {
            showCopySuccess(buttonElement);
          })
          .catch(err => {
            console.error('Clipboard API failed:', err);
            fallbackCopyToClipboard(text, buttonElement);
          });
      } else {
        // Fallback for older browsers or non-HTTPS
        fallbackCopyToClipboard(text, buttonElement);
      }
    }

    // Fallback copy method for older browsers
    function fallbackCopyToClipboard(text, buttonElement) {
      try {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);

        if (successful) {
          showCopySuccess(buttonElement);
        } else {
          throw new Error('execCommand failed');
        }
      } catch (err) {
        console.error('Fallback copy failed:', err);
        showToast('Copy failed. Please copy manually.', 'error');

        // Show text in a prompt as last resort
        prompt('Copy this text:', text);
      }
    }

    // Show copy success animation
    function showCopySuccess(buttonElement) {
      const originalHTML = buttonElement.innerHTML;
      buttonElement.innerHTML = '✅';
      buttonElement.classList.add('copy-success');

      setTimeout(() => {
        buttonElement.innerHTML = originalHTML;
        buttonElement.classList.remove('copy-success');
      }, 1500);

      showToast('Message copied to clipboard!', 'success');
    }

    // Enhanced toast notification with new toast manager
    function showToast(message, type = 'success', duration = 3000, actions = []) {
      // Use new toast manager if available, fallback to old system
      if (window.toastManager) {
        const toastType = type === 'error' ? 'error' : type === 'warning' ? 'warning' : type === 'info' ? 'info' : 'success';
        return window.toastManager.show(message, toastType, duration, actions);
      } else {
        // Fallback to old toast system
        toastMessage.textContent = message;
        toast.classList.remove('bg-green-500', 'bg-red-500');
        toast.classList.add(type === 'success' ? 'bg-green-500' : 'bg-red-500');
        toast.classList.remove('hidden');
        
        setTimeout(() => {
          toast.classList.add('hidden');
        }, duration);
      }
    }

    // Validate prompt
    function validatePrompt(prompt) {
      if (prompt.trim() === '') {
        showToast('Please enter a message before sending.', 'error');
        return false;
      }
      // Removed character limit - allow longer messages
      
      
      return true;
    }

    // Image upload handling
    const imageUpload = document.getElementById('image-upload');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeImageBtn = document.getElementById('remove-image');
    let selectedImage = null;
    
    // Handle image selection
    imageUpload.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        selectedImage = file;
        const reader = new FileReader();
        reader.onload = (e) => {
          imagePreview.src = e.target.result;
          imagePreviewContainer.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
      }
    });
    
    // Handle image removal
    removeImageBtn.addEventListener('click', () => {
      selectedImage = null;
      imageUpload.value = '';
      imagePreviewContainer.classList.add('hidden');
    });
    
    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const prompt = promptInput.value.trim();
      if (!validatePrompt(prompt)) return;
      
      // Add message with image if one is selected
      addMessage(prompt, 'user');
      promptInput.value = '';
      
      startTypingAnimation();
      sendButton.disabled = true;
      
      try {
        let res;
        
        // Create a temporary message for streaming responses
        const tempMessageId = Date.now().toString();
        let isFirstChunk = true;
        let streamingMessage = null;
        
        // Enable streaming for better user experience
        const useStreaming = true;
        
        // Check if an image is selected
        if (selectedImage) {
          // Create FormData for multipart/form-data request
          const formData = new FormData();
          formData.append('prompt', prompt);
          formData.append('image', selectedImage);
          
          // Send multimodal request (streaming not supported for multimodal yet)
          res = await fetch('AIModelAPI.php', {
            method: 'POST',
            body: formData,
          });
          
          // Clear the image after sending
          selectedImage = null;
          imageUpload.value = '';
          imagePreviewContainer.classList.add('hidden');
          
          const data = await res.json();
          
          if (data.error) {
            showToast(data.error, 'error');
            return;
          }
          
          // Check if the response contains an image
          if (data.hasImage && data.imageData) {
            // Create image data URL
            const imageUrl = `data:${data.imageData.mime_type};base64,${data.imageData.data}`;
            addMessage(data.response, 'assistant', imageUrl);
          } else {
            addMessage(data.response, 'assistant');
          }
          
          // Show notification if tab is hidden
          if (window.showNotificationOnResponse && window.notificationManager) {
            window.notificationManager.showNotificationIfHidden('AI Response Ready', {
              body: data.response.substring(0, 100) + (data.response.length > 100 ? '...' : ''),
              tag: 'ai-response'
            });
            window.showNotificationOnResponse = false;
          }
        } else {
          // For text-only requests, use streaming
          // Add an empty assistant message that will be updated with streaming content
          addMessage('', 'assistant');
          streamingMessage = document.querySelector('.msg.assistant:last-child .message-content');
          
          try {
            // First, prepare the server for streaming by sending the prompt
            const prepareResponse = await fetch('AIModelAPI.php?prepareStream=true', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ prompt }),
            });
            
            // Check if preparation was successful
            const prepareData = await prepareResponse.json();
            if (prepareData.error) {
              throw new Error(prepareData.error);
            }
            
            // Get the stream token for authentication
            const streamToken = prepareData.stream_token;
            
            // Enhanced EventSource with retry mechanism
            let eventSource = null;
            let fullResponse = '';
            let retryCount = 0;
            const maxRetries = 2;

            function createEventSource() {
              eventSource = new EventSource(`AIModelAPI.php?stream=true&token=${encodeURIComponent(streamToken)}`);

              // Handle incoming stream data
              eventSource.onmessage = (event) => {
                if (event.data === '[DONE]') {
                  eventSource.close();

                  // Process the complete response for code blocks
                  if (fullResponse.includes('```')) {
                    processCodeBlocks(fullResponse, streamingMessage);
                  } else {
                    // Update the message content in the messages array
                    const lastMessage = messages[messages.length - 1];
                    if (lastMessage && lastMessage.role === 'assistant') {
                      lastMessage.content = fullResponse;
                      saveMessages();
                    }
                  }

                  return;
                }

                try {
                  const data = JSON.parse(event.data);

                  if (data.chunk) {
                    // Accumulate the full response
                    fullResponse += data.chunk;

                    // Update the streaming message with new content
                    if (streamingMessage) {
                      // Simple update for streaming experience
                      streamingMessage.textContent = fullResponse;

                      // Scroll to bottom to show new content
                      chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                  }

                  // Handle image if available
                  if (data.hasImage && data.imageData) {
                    const imageUrl = `data:${data.imageData.mime_type};base64,${data.imageData.data}`;
                    // Find the message container and add the image
                    const messageContainer = streamingMessage?.parentElement;

                    if (messageContainer) {
                      // Create image element
                      const imageContainer = document.createElement('div');
                      imageContainer.className = 'mb-2';

                      const img = document.createElement('img');
                      img.src = imageUrl;
                      img.className = 'rounded-lg max-w-full max-h-48 object-contain';
                      img.alt = 'Generated image';

                      imageContainer.appendChild(img);
                      messageContainer.insertBefore(imageContainer, streamingMessage);
                    }
                  }
                } catch (e) {
                  console.error('Error parsing stream data:', e);
                }
              };

              // Enhanced error handling
              eventSource.onerror = (error) => {
                console.error('EventSource error:', error);
                eventSource.close();

                // Retry logic
                if (retryCount < maxRetries) {
                  retryCount++;
                  console.log(`Retrying EventSource connection (${retryCount}/${maxRetries})`);
                  showToast(`Connection lost. Retrying... (${retryCount}/${maxRetries})`, 'warning');

                  // Retry after a short delay
                  setTimeout(() => {
                    createEventSource();
                  }, 1000 * retryCount);
                } else {
                  console.log('Max retries reached, falling back to standard request');
                  showToast('Streaming failed. Falling back to standard request.', 'error');

                  // Fallback to standard request
                  fallbackToStandardRequest(prompt, streamingMessage);
                }
              };

              // Handle connection open
              eventSource.onopen = () => {
                console.log('EventSource connection opened');
                retryCount = 0; // Reset retry count on successful connection
              };
            }

            // Start the EventSource connection
            createEventSource();
          } catch (error) {
            console.error('Error:', error);
            showToast('Failed to process your message. Please try again.', 'error');
            
            // Fallback to standard request
            fallbackToStandardRequest(prompt, streamingMessage);
          } finally {
            stopTypingAnimation();
            sendButton.disabled = false;
          }
        }
      } catch (error) {
        showToast('Failed to process your message. Please try again.', 'error');
        console.error('Error:', error);
      } finally {
        stopTypingAnimation();
        sendButton.disabled = false;
      }
    });

    // Character counter removed - allow unlimited length

    // Handle voice input with enhanced error handling
    micButton.addEventListener('click', () => {
      if (!isListening) {
        startVoiceRecognition();
      } else {
        stopVoiceRecognition();
      }
    });

    let currentRecognition = null;

    function startVoiceRecognition() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

      if (!SpeechRecognition) {
        showToast('Speech recognition is not supported in your browser. Try Chrome or Edge.', 'error');
        return;
      }

      try {
        currentRecognition = new SpeechRecognition();
        currentRecognition.lang = 'en-US';
        currentRecognition.continuous = false;
        currentRecognition.interimResults = true;
        currentRecognition.maxAlternatives = 1;

        currentRecognition.onstart = () => {
          isListening = true;
          micButton.classList.add('mic-active');
          micButton.classList.remove('bg-gray-100', 'dark:bg-gray-700');
          micButton.classList.add('bg-red-500', 'text-white');
          micButton.innerHTML = '🛑';
          showToast('Listening... Click to stop', 'info');
        };

        currentRecognition.onresult = (event) => {
          const transcript = Array.from(event.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join('');

          promptInput.value = transcript;
        };

        currentRecognition.onend = () => {
          stopVoiceRecognition();
        };

        currentRecognition.onerror = (event) => {
          console.error('Speech recognition error:', event.error);
          stopVoiceRecognition();

          let errorMessage = 'Voice recognition failed. ';
          switch(event.error) {
            case 'no-speech':
              errorMessage += 'No speech detected. Please try again.';
              break;
            case 'audio-capture':
              errorMessage += 'Microphone not accessible.';
              break;
            case 'not-allowed':
              errorMessage += 'Microphone permission denied.';
              break;
            default:
              errorMessage += 'Please try again.';
          }
          showToast(errorMessage, 'error');
        };

        currentRecognition.start();
      } catch (error) {
        console.error('Failed to start speech recognition:', error);
        showToast('Failed to start voice recognition. Please try again.', 'error');
        stopVoiceRecognition();
      }
    }

    function stopVoiceRecognition() {
      if (currentRecognition) {
        currentRecognition.stop();
        currentRecognition = null;
      }

      isListening = false;
      micButton.classList.remove('mic-active');
      micButton.classList.remove('bg-red-500', 'text-white');
      micButton.classList.add('bg-gray-100', 'dark:bg-gray-700');
      micButton.innerHTML = '🎤';
    }

    // Handle theme toggle
    themeToggle.addEventListener('click', () => {
      document.documentElement.classList.toggle('dark');
      const isDark = document.documentElement.classList.contains('dark');
      localStorage.setItem('darkMode', isDark);
      
      // Switch Prism.js themes based on mode
      switchPrismTheme(isDark);
    });

    // Switch Prism.js themes
    function switchPrismTheme(isDark) {
      const lightTheme = document.getElementById('prism-light-theme');
      const darkTheme = document.getElementById('prism-dark-theme');
      
      if (lightTheme && darkTheme) {
        if (isDark) {
          lightTheme.disabled = true;
          darkTheme.disabled = false;
        } else {
          lightTheme.disabled = false;
          darkTheme.disabled = true;
        }
        
        // Re-highlight all code blocks
        setTimeout(() => {
          if (window.Prism && typeof Prism.highlightAll === 'function') {
            Prism.highlightAll();
          }
        }, 100);
      }
    }

    // Handle clear chat
    clearChatButton.addEventListener('click', () => {
      messages = [];
      localStorage.removeItem('chatMessages');
      messagesContainer.classList.add('hidden');
      welcomeMessage.classList.remove('hidden');
      showToast('Chat history cleared.');
    });

    // Handle toast close
    closeToast.addEventListener('click', () => {
      toast.classList.add('hidden');
    });

    // Scroll functions
    function scrollToTop() {
      chatContainer.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }

    function scrollToBottom() {
      chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
      });
    }

    // Update scroll buttons visibility
    function updateScrollButtonsVisibility() {
      // Only show scroll buttons if there's enough content to scroll
      if (chatContainer.scrollHeight > chatContainer.clientHeight) {
        scrollTopBtn.style.display = 'flex';
        scrollBottomBtn.style.display = 'flex';
      } else {
        scrollTopBtn.style.display = 'none';
        scrollBottomBtn.style.display = 'none';
      }
    }
    

    
    // Fallback to standard request when streaming fails
    async function fallbackToStandardRequest(prompt, messageElement) {
      try {
        // Add a small delay before trying the fallback to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Try the main API first
        let res = await fetch('AIModelAPI.php', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ prompt }),
        });

        // If main API fails, try simple API
        if (!res.ok) {
          console.log('Main API failed, trying simple API...');
          showToast('Trying alternative API...', 'warning');

          res = await fetch('ask.php', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt }),
          });
        }
        
        // Handle HTTP errors
        if (res.status === 429) {
          showToast("Rate limit exceeded. Please wait a moment before trying again.", 'error');
          if (messageElement) {
            messageElement.textContent = "Sorry, you've sent too many messages. Please wait a moment before trying again.";
          }
          return;
        }
        
        const data = await res.json();

        // Handle different API response formats
        let responseText = '';
        if (data.success && data.response) {
          // Simple API format
          responseText = data.response;
        } else if (data.response) {
          // Main API format
          responseText = data.response;
        } else if (data.error) {
          showToast(data.error, 'error');
          if (messageElement) {
            messageElement.textContent = "Sorry, there was an error processing your request.";
          }
          return;
        } else {
          throw new Error('Invalid response format');
        }

        // Update the message with the response
        if (messageElement) {
          if (responseText.includes('```')) {
            processCodeBlocks(responseText, messageElement);
          } else {
            messageElement.textContent = responseText;
          }
          
          // IMPORTANT: Update the messages array and save to localStorage
          const lastMessage = messages[messages.length - 1];
          if (lastMessage && lastMessage.role === 'assistant') {
            lastMessage.content = responseText;
            if (data.hasImage && data.imageData) {
              lastMessage.hasImage = true;
              lastMessage.imageData = `data:${data.imageData.mime_type};base64,${data.imageData.data}`;
            }
            saveMessages();
          }
          
          // Handle image if available
          if (data.hasImage && data.imageData) {
            const imageUrl = `data:${data.imageData.mime_type};base64,${data.imageData.data}`;
            const messageContainer = messageElement.parentElement;
            
            const imageContainer = document.createElement('div');
            imageContainer.className = 'mb-2';
            
            const img = document.createElement('img');
            img.src = imageUrl;
            img.className = 'rounded-lg max-w-full max-h-48 object-contain';
            img.alt = 'Generated image';
            
            imageContainer.appendChild(img);
            messageContainer.insertBefore(imageContainer, messageElement);
          }
        }
      } catch (error) {
        console.error('Fallback error:', error);
        if (messageElement) {
          messageElement.textContent = "Sorry, there was an error processing your request. Please try again.";
        }
      }
    }

    // Scroll button event listeners
    scrollTopBtn.addEventListener('click', scrollToTop);
    scrollBottomBtn.addEventListener('click', scrollToBottom);

    // Listen for scroll events to update button visibility
    chatContainer.addEventListener('scroll', () => {
      const isAtTop = chatContainer.scrollTop === 0;
      const isAtBottom = chatContainer.scrollTop + chatContainer.clientHeight >= chatContainer.scrollHeight - 10;
      
      scrollTopBtn.style.opacity = isAtTop ? '0.5' : '1';
      scrollBottomBtn.style.opacity = isAtBottom ? '0.5' : '1';
    });

    // === NEW FUNCTIONALITY ===
    
    // Quick Reply functionality
    quickReplyButtons.forEach(button => {
      button.addEventListener('click', function() {
        const prompt = this.textContent.trim();
        promptInput.value = prompt;
        promptInput.focus();
      });
    });

    // Conversation Sidebar functionality
    openSidebarBtn.addEventListener('click', function() {
      conversationSidebar.classList.remove('-translate-x-full');
      loadConversationList();
    });

    closeSidebarBtn.addEventListener('click', function() {
      conversationSidebar.classList.add('-translate-x-full');
    });

    // New Chat functionality
    newChatBtn.addEventListener('click', function() {
      if (messages.length > 0 && confirm('Start a new conversation? Current chat will be saved automatically.')) {
        // Auto-save current conversation
        if (messages.length > 0) {
          saveCurrentConversation();
        }
        
        // Start new chat
        messages = [];
        currentConversationId = null;
        localStorage.removeItem('chatMessages');
        messagesContainer.classList.add('hidden');
        welcomeMessage.classList.remove('hidden');
        showToast('Started a new conversation', 'success');
        conversationSidebar.classList.add('-translate-x-full');
      }
    });

    // Save Conversation functionality
    saveConversationBtn.addEventListener('click', function() {
      if (messages.length === 0) {
        showToast('No messages to save', 'error');
        return;
      }
      
      const title = prompt('Enter a name for this conversation:') || generateConversationTitle();
      if (title) {
        const conversation = saveConversationBranch(title);
        showToast(`Conversation "${title}" saved!`, 'success');
        loadConversationList();
      }
    });

    // Export Chat functionality
    const exportChatBtn = document.getElementById('export-chat-btn');
    const exportModal = document.getElementById('export-modal');
    const closeExportModal = document.getElementById('close-export-modal');
    const cancelExport = document.getElementById('cancel-export');
    const confirmExport = document.getElementById('confirm-export');
    const chatSelection = document.getElementById('chat-selection');
    
    exportChatBtn.addEventListener('click', function() {
      // Populate chat selection dropdown
      populateChatSelection();
      exportModal.classList.remove('hidden');
    });
    
    closeExportModal.addEventListener('click', function() {
      exportModal.classList.add('hidden');
    });
    
    cancelExport.addEventListener('click', function() {
      exportModal.classList.add('hidden');
    });
    
    confirmExport.addEventListener('click', function() {
      handleExport();
    });

    // Search functionality
    searchToggle.addEventListener('click', function() {
      searchModal.classList.remove('hidden');
      searchInput.focus();
    });

    closeSearchBtn.addEventListener('click', function() {
      searchModal.classList.add('hidden');
      searchInput.value = '';
      searchResults.innerHTML = '<div class="text-center text-gray-500 dark:text-gray-400">Type to search through your conversation history...</div>';
    });

    // Search input functionality
    searchInput.addEventListener('input', function() {
      const query = this.value.trim().toLowerCase();
      if (query.length === 0) {
        searchResults.innerHTML = '<div class="text-center text-gray-500 dark:text-gray-400">Type to search through your conversation history...</div>';
        return;
      }
      
      if (query.length < 2) return;
      
      searchConversations(query);
    });

    // Close modals on click outside
    searchModal.addEventListener('click', function(e) {
      if (e.target === this) {
        this.classList.add('hidden');
      }
    });

    // Helper Functions for New Features
    function generateConversationTitle() {
      if (messages.length > 0) {
        const firstUserMessage = messages.find(m => m.role === 'user');
        if (firstUserMessage) {
          return firstUserMessage.content.substring(0, 30) + (firstUserMessage.content.length > 30 ? '...' : '');
        }
      }
      return `Chat ${new Date().toLocaleDateString()}`;
    }

    function saveCurrentConversation() {
      if (messages.length === 0) return;
      
      const title = generateConversationTitle();
      return saveConversationBranch(title);
    }

    function saveConversationBranch(title) {
      const conversation = {
        id: currentConversationId || Date.now().toString(),
        title: title,
        messages: [...messages],
        timestamp: new Date(),
        messageCount: messages.length
      };
      
      // Update or add conversation
      const existingIndex = conversationBranches.findIndex(c => c.id === conversation.id);
      if (existingIndex !== -1) {
        conversationBranches[existingIndex] = conversation;
      } else {
        conversationBranches.unshift(conversation);
      }
      
      // Keep only last 50 conversations
      if (conversationBranches.length > 50) {
        conversationBranches = conversationBranches.slice(0, 50);
      }
      
      localStorage.setItem('conversationBranches', JSON.stringify(conversationBranches));
      currentConversationId = conversation.id;
      
      return conversation;
    }

    function loadConversationBranch(conversationId) {
      const conversation = conversationBranches.find(c => c.id === conversationId);
      if (conversation) {
        messages = [...conversation.messages];
        currentConversationId = conversationId;
        localStorage.setItem('chatMessages', JSON.stringify(messages));
        
        if (messages.length > 0) {
          welcomeMessage.classList.add('hidden');
          messagesContainer.classList.remove('hidden');
          renderMessages();
        }
        
        showToast(`Loaded conversation: ${conversation.title}`, 'success');
        conversationSidebar.classList.add('-translate-x-full');
      }
    }

    function loadConversationList() {
      conversationList.innerHTML = '';
      
      if (conversationBranches.length === 0) {
        conversationList.innerHTML = '<div class="text-center text-gray-500 dark:text-gray-400 py-4">No saved conversations</div>';
        return;
      }
      
      conversationBranches.forEach(conversation => {
        const item = document.createElement('button');
        item.className = 'w-full text-left p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center justify-between group transition-colors';
        
        item.innerHTML = `
          <div class="flex items-center flex-1 min-w-0">
            <svg class="h-4 w-4 mr-2 text-gray-500 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <div class="flex-1 min-w-0">
              <div class="truncate font-medium">${conversation.title}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">${conversation.messageCount} messages • ${new Date(conversation.timestamp).toLocaleDateString()}</div>
            </div>
          </div>
          <button class="delete-conversation opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 p-1 ml-2" data-id="${conversation.id}">
            <svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        `;
        
        item.addEventListener('click', function(e) {
          if (e.target.closest('.delete-conversation')) {
            e.stopPropagation();
            deleteConversation(conversation.id);
          } else {
            loadConversationBranch(conversation.id);
          }
        });
        
        conversationList.appendChild(item);
      });
    }

    function deleteConversation(conversationId) {
      if (confirm('Are you sure you want to delete this conversation?')) {
        conversationBranches = conversationBranches.filter(c => c.id !== conversationId);
        localStorage.setItem('conversationBranches', JSON.stringify(conversationBranches));
        loadConversationList();
        showToast('Conversation deleted', 'success');
      }
    }

    function searchConversations(query) {
      const results = [];
      
      // Search in current messages
      messages.forEach((message, index) => {
        if (message.content.toLowerCase().includes(query)) {
          results.push({
            type: 'current',
            content: message.content,
            role: message.role,
            index: index,
            timestamp: message.timestamp
          });
        }
      });
      
      // Search in saved conversations
      conversationBranches.forEach(conversation => {
        conversation.messages.forEach(message => {
          if (message.content.toLowerCase().includes(query)) {
            results.push({
              type: 'saved',
              content: message.content,
              role: message.role,
              conversationTitle: conversation.title,
              conversationId: conversation.id,
              timestamp: message.timestamp
            });
          }
        });
      });
      
      displaySearchResults(results, query);
    }

    function displaySearchResults(results, query) {
      if (results.length === 0) {
        searchResults.innerHTML = '<div class="text-center text-gray-500 dark:text-gray-400">No results found</div>';
        return;
      }
      
      searchResults.innerHTML = '';
      
      results.slice(0, 20).forEach(result => {
        const item = document.createElement('div');
        item.className = 'p-3 border border-gray-200 dark:border-gray-700 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer';
        
        const highlightedContent = highlightText(result.content, query);
        
        item.innerHTML = `
          <div class="flex items-start space-x-2">
            <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs ${result.role === 'user' ? 'bg-primary-100 text-primary-600' : 'bg-gray-100 text-gray-600'}">
              ${result.role === 'user' ? 'U' : 'AI'}
            </div>
            <div class="flex-1">
              <div class="text-sm">${highlightedContent}</div>
              <div class="text-xs text-gray-500 mt-1">
                ${result.type === 'saved' ? `From: ${result.conversationTitle} • ` : 'Current chat • '}
                ${new Date(result.timestamp).toLocaleDateString()}
              </div>
            </div>
          </div>
        `;
        
        item.addEventListener('click', function() {
          if (result.type === 'saved') {
            loadConversationBranch(result.conversationId);
            searchModal.classList.add('hidden');
          } else {
            // Scroll to message in current chat
            const messageElements = document.querySelectorAll('.msg');
            if (messageElements[result.index]) {
              messageElements[result.index].scrollIntoView({ behavior: 'smooth', block: 'center' });
              messageElements[result.index].classList.add('bg-yellow-100', 'dark:bg-yellow-900');
              setTimeout(() => {
                messageElements[result.index].classList.remove('bg-yellow-100', 'dark:bg-yellow-900');
              }, 2000);
            }
            searchModal.classList.add('hidden');
          }
        });
        
        searchResults.appendChild(item);
      });
    }

    function highlightText(text, query) {
      const regex = new RegExp(`(${query})`, 'gi');
      return text.substring(0, 200).replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800">$1</mark>') + (text.length > 200 ? '...' : '');
    }

    function populateChatSelection() {
      // Clear existing options except the first one
      chatSelection.innerHTML = '<option value="current">Current Chat</option>';
      
      // Add saved conversations
      conversationBranches.forEach((conversation, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = `${conversation.title || 'Untitled Chat'} (${conversation.messages.length} messages)`;
        chatSelection.appendChild(option);
      });
    }
    
    function handleExport() {
      const selectedChat = chatSelection.value;
      const exportFormat = document.querySelector('input[name="export-format"]:checked').value;
      
      let chatData;
      let chatTitle;
      
      if (selectedChat === 'current') {
        chatData = messages;
        chatTitle = 'Current Chat';
      } else {
        const conversationIndex = parseInt(selectedChat);
        chatData = conversationBranches[conversationIndex].messages;
        chatTitle = conversationBranches[conversationIndex].title || 'Saved Chat';
      }
      
      if (chatData.length === 0) {
        showToast('Selected chat is empty!', 'error');
        return;
      }
      
      // Export based on format
      switch (exportFormat) {
        case 'txt':
          exportAsText(chatData, chatTitle);
          break;
        case 'pdf':
          exportAsPDF(chatData, chatTitle);
          break;
        case 'html':
          exportAsHTML(chatData, chatTitle);
          break;
      }
      
      exportModal.classList.add('hidden');
    }
    
    function exportAsText(chatData, title) {
      let textContent = `${title}\n`;
      textContent += `Exported on: ${new Date().toLocaleString()}\n`;
      textContent += '=' .repeat(50) + '\n\n';
      
      chatData.forEach((message, index) => {
        const role = message.role === 'user' ? 'User' : 'AI Assistant';
        const timestamp = message.timestamp ? new Date(message.timestamp).toLocaleString() : 'Unknown';
        
        textContent += `${index + 1}. ${role} (${timestamp}):\n`;
        textContent += message.content + '\n\n';
        
        if (message.hasImage) {
          textContent += '[Image attached]\n\n';
        }
      });
      
      const blob = new Blob([textContent], { type: 'text/plain' });
      downloadFile(blob, `${title.replace(/[^a-z0-9]/gi, '_')}.txt`);
      showToast('Chat exported as text file!', 'success');
    }
    
    function exportAsHTML(chatData, title) {
      let htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .message { margin-bottom: 20px; padding: 15px; border-radius: 10px; }
        .user { background-color: #e3f2fd; text-align: right; }
        .assistant { background-color: #f5f5f5; }
        .role { font-weight: bold; margin-bottom: 5px; }
        .timestamp { font-size: 0.8em; color: #666; }
        .content { margin-top: 10px; white-space: pre-wrap; }
        img { max-width: 100%; height: auto; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>${title}</h1>
        <p>Exported on: ${new Date().toLocaleString()}</p>
    </div>
`;
      
      chatData.forEach((message, index) => {
        const role = message.role === 'user' ? 'User' : 'AI Assistant';
        const timestamp = message.timestamp ? new Date(message.timestamp).toLocaleString() : 'Unknown';
        
        htmlContent += `
    <div class="message ${message.role}">
        <div class="role">${role}</div>
        <div class="timestamp">${timestamp}</div>
        ${message.hasImage && message.imageData ? `<img src="${message.imageData}" alt="User uploaded image">` : ''}
        <div class="content">${message.content.replace(/\n/g, '<br>')}</div>
    </div>
`;
      });
      
      htmlContent += `
</body>
</html>`;
      
      const blob = new Blob([htmlContent], { type: 'text/html' });
      downloadFile(blob, `${title.replace(/[^a-z0-9]/gi, '_')}.html`);
      showToast('Chat exported as HTML file!', 'success');
    }
    
    function exportAsPDF(chatData, title) {
      try {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        // Set font and title
        doc.setFontSize(20);
        doc.text(title, 20, 20);
        
        doc.setFontSize(10);
        doc.text(`Exported on: ${new Date().toLocaleString()}`, 20, 30);
        
        let yPosition = 50;
        const pageHeight = doc.internal.pageSize.height;
        const margin = 20;
        const maxWidth = doc.internal.pageSize.width - 2 * margin;
        
        chatData.forEach((message, index) => {
          // Check if we need a new page
          if (yPosition > pageHeight - 40) {
            doc.addPage();
            yPosition = 20;
          }
          
          const role = message.role === 'user' ? 'User' : 'AI Assistant';
          const timestamp = message.timestamp ? new Date(message.timestamp).toLocaleString() : 'Unknown';
          
          // Add role and timestamp
          doc.setFontSize(12);
          doc.setFont(undefined, 'bold');
          doc.text(`${index + 1}. ${role} (${timestamp})`, margin, yPosition);
          yPosition += 8;
          
          // Add content
          doc.setFont(undefined, 'normal');
          doc.setFontSize(10);
          
          // Split text to fit page width
          const lines = doc.splitTextToSize(message.content, maxWidth);
          doc.text(lines, margin, yPosition);
          yPosition += lines.length * 5 + 10;
          
          if (message.hasImage) {
            doc.text('[Image attached]', margin, yPosition);
            yPosition += 8;
          }
          
          yPosition += 5; // Extra spacing between messages
        });
        
        // Save the PDF
        doc.save(`${title.replace(/[^a-z0-9]/gi, '_')}.pdf`);
        showToast('Chat exported as PDF!', 'success');
        
      } catch (error) {
        console.error('PDF export error:', error);
        showToast('PDF export failed. Try HTML format instead.', 'error');
        exportAsHTML(chatData, title);
      }
    }
    
    function downloadFile(blob, filename) {
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
      // Ctrl/Cmd + K for search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        searchModal.classList.remove('hidden');
        searchInput.focus();
      }
      
      // Ctrl/Cmd + N for new chat
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        newChatBtn.click();
      }
      
      // Ctrl/Cmd + S to save conversation
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveConversationBtn.click();
      }
      
      // Escape to close modals
      if (e.key === 'Escape') {
        searchModal.classList.add('hidden');
        conversationSidebar.classList.add('-translate-x-full');
      }
    });

    // Enhanced Typing Indicator Functions
    function showTypingIndicator(message = 'AI is thinking...', showProgress = false) {
      typingText.textContent = message;
      
      if (showProgress) {
        typingProgress.classList.remove('hidden');
        animateProgress();
      } else {
        typingProgress.classList.add('hidden');
      }
      
      loadingIndicator.classList.remove('hidden');
      
      // Scroll to show typing indicator
      setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }, 100);
    }

    function hideTypingIndicator() {
      loadingIndicator.classList.add('hidden');
      typingProgress.classList.add('hidden');
    }

    function updateTypingIndicator(message) {
      if (!loadingIndicator.classList.contains('hidden')) {
        typingText.textContent = message;
      }
    }

    function animateProgress() {
      const progressBar = typingProgress.querySelector('.bg-primary-500');
      let width = 0;
      const interval = setInterval(() => {
        width += Math.random() * 10;
        if (width >= 90) {
          width = 90;
          clearInterval(interval);
        }
        progressBar.style.width = width + '%';
      }, 200);
    }

    // Enhanced typing messages for different scenarios
    const typingMessages = [
      'AI is thinking...',
      'Processing your request...',
      'Analyzing the context...',
      'Generating response...',
      'Almost ready...',
      'Finalizing answer...'
    ];

    function showRandomTypingMessage() {
      const randomMessage = typingMessages[Math.floor(Math.random() * typingMessages.length)];
      updateTypingIndicator(randomMessage);
    }

    // Auto-save current conversation periodically
    setInterval(() => {
      if (messages.length > 0 && currentConversationId) {
        saveCurrentConversation();
      }
    }, 30000); // Auto-save every 30 seconds

    // Cycle through typing messages
    let typingMessageInterval;

    function startTypingAnimation() {
      showRandomTypingMessage();
      typingMessageInterval = setInterval(showRandomTypingMessage, 2000);
    }

    function stopTypingAnimation() {
      if (typingMessageInterval) {
        clearInterval(typingMessageInterval);
        typingMessageInterval = null;
      }
      hideTypingIndicator();
    }

    // === LANGUAGE SELECTOR FUNCTIONALITY ===
    const languageToggle = document.getElementById('language-toggle');
    const languageMenu = document.getElementById('language-menu');
    const languageOptions = document.querySelectorAll('.language-option');
    let currentLanguage = 'en';

    // Language toggle functionality
    languageToggle.addEventListener('click', function(e) {
      e.stopPropagation();
      languageMenu.classList.toggle('opacity-0');
      languageMenu.classList.toggle('invisible');
    });

    // Close language menu when clicking outside
    document.addEventListener('click', function(e) {
      if (!languageToggle.contains(e.target) && !languageMenu.contains(e.target)) {
        languageMenu.classList.add('opacity-0');
        languageMenu.classList.add('invisible');
      }
    });

    // Language option selection
    languageOptions.forEach(option => {
      option.addEventListener('click', function(e) {
        e.stopPropagation();
        const selectedLang = this.getAttribute('data-lang');
        setLanguage(selectedLang);
        languageMenu.classList.add('opacity-0');
        languageMenu.classList.add('invisible');
      });
    });

    // Load current language from API
    async function loadCurrentLanguage() {
      try {
        console.log('Loading current language...');
        const response = await fetch('language-selector.php', {
          method: 'GET'
        });
        console.log('Response received:', response.status);
        const data = await response.json();
        console.log('Data parsed:', data);
        
        if (data.status === 'success') {
          currentLanguage = data.current_language;
          console.log('Current language set to:', currentLanguage);
          updateLanguageUI();
          console.log(`Language loaded: ${data.language_name}`);
        } else {
          console.log('Language load failed:', data);
        }
      } catch (error) {
        console.error('Failed to load language:', error);
        currentLanguage = 'en'; // Default to English
      }
    }

    // Set language via API
    async function setLanguage(lang) {
      try {
        console.log('Setting language to:', lang);
        const response = await fetch('language-selector.php', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ language: lang })
        });
        
        console.log('Language set response:', response.status);
        const data = await response.json();
        console.log('Language set data:', data);
        
        if (data.status === 'success') {
          currentLanguage = lang;
          console.log('Language updated to:', currentLanguage);
          updateLanguageUI();
          showToast(data.message, 'success');
          
          // Apply language-specific changes to UI
          applyLanguageChanges(lang);
        } else {
          console.log('Language set failed:', data);
          showToast(data.message || 'Failed to set language', 'error');
        }
      } catch (error) {
        console.error('Failed to set language:', error);
        showToast('Failed to set language. Please try again.', 'error');
      }
    }

    // Update language UI indicators
    function updateLanguageUI() {
      console.log('Updating language UI for:', currentLanguage);
      console.log('Language options found:', languageOptions.length);
      
      languageOptions.forEach((option, index) => {
        const optionLang = option.getAttribute('data-lang');
        console.log(`Option ${index}: ${optionLang}, Current: ${currentLanguage}`);
        
        if (optionLang === currentLanguage) {
          option.classList.add('bg-primary-100', 'dark:bg-primary-900', 'text-primary-700', 'dark:text-primary-300');
          console.log(`Applied active styles to ${optionLang}`);
        } else {
          option.classList.remove('bg-primary-100', 'dark:bg-primary-900', 'text-primary-700', 'dark:text-primary-300');
        }
      });
    }

    // Apply language-specific changes
    function applyLanguageChanges(lang) {
      // Basic language-specific UI text changes
      const translations = {
        'en': {
          'welcome-title': 'Welcome to AI Chat Assistant',
          'welcome-subtitle': 'Start a conversation with our AI assistant. Ask questions, get help, or just chat!',
          'placeholder': 'Type your message here...'
        },
        'es': {
          'welcome-title': 'Bienvenido al Asistente de Chat IA',
          'welcome-subtitle': '¡Inicia una conversación con nuestro asistente de IA. Haz preguntas, obtén ayuda o simplemente conversa!',
          'placeholder': 'Escribe tu mensaje aquí...'
        },
        'fr': {
          'welcome-title': 'Bienvenue dans l\'Assistant de Chat IA',
          'welcome-subtitle': 'Commencez une conversation avec notre assistant IA. Posez des questions, obtenez de l\'aide ou discutez simplement !',
          'placeholder': 'Tapez votre message ici...'
        },
        'de': {
          'welcome-title': 'Willkommen beim KI-Chat-Assistenten',
          'welcome-subtitle': 'Beginnen Sie ein Gespräch mit unserem KI-Assistenten. Stellen Sie Fragen, holen Sie sich Hilfe oder unterhalten Sie sich einfach!',
          'placeholder': 'Geben Sie hier Ihre Nachricht ein...'
        },
        'hi': {
          'welcome-title': 'AI चैट असिस्टेंट में आपका स्वागत है',
          'welcome-subtitle': 'हमारे AI असिस्टेंट के साथ बातचीत शुरू करें। सवाल पूछें, मदद लें या बस चैट करें!',
          'placeholder': 'यहाँ अपना संदेश लिखें...'
        },
        'zh': {
          'welcome-title': '欢迎使用AI聊天助手',
          'welcome-subtitle': '与我们的AI助手开始对话。提问、获取帮助或只是聊天！',
          'placeholder': '在此输入您的消息...'
        },
        'ja': {
          'welcome-title': 'AIチャットアシスタントへようこそ',
          'welcome-subtitle': 'AIアシスタントとの会話を始めましょう。質問したり、ヘルプを求めたり、ただチャットしたりしてください！',
          'placeholder': 'ここにメッセージを入力...'
        }
      };

      const langTexts = translations[lang] || translations['en'];
      
      // Update welcome message texts
      const welcomeTitle = document.querySelector('#welcome-message h2');
      const welcomeSubtitle = document.querySelector('#welcome-message p');
      const promptPlaceholder = document.getElementById('prompt-input');
      
      if (welcomeTitle) welcomeTitle.textContent = langTexts['welcome-title'];
      if (welcomeSubtitle) welcomeSubtitle.textContent = langTexts['welcome-subtitle'];
      if (promptPlaceholder) promptPlaceholder.placeholder = langTexts['placeholder'];
      
      // Store language preference
      localStorage.setItem('preferredLanguage', lang);
    }

    // Quick prompt function for capability cards
    function setQuickPrompt(prompt) {
      promptInput.value = prompt;
      promptInput.focus();
      // Add a subtle highlight effect
      promptInput.classList.add('ring-2', 'ring-primary-500');
      setTimeout(() => {
        promptInput.classList.remove('ring-2', 'ring-primary-500');
      }, 1000);
    }

    // Check for dark mode preference and apply theme
    if (localStorage.getItem('darkMode') === 'true' || 
        (!localStorage.getItem('darkMode') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
      switchPrismTheme(true);
    } else {
      switchPrismTheme(false);
    }

    // Initialize
    loadMessages();
    updateScrollButtonsVisibility();
    loadConversationList();
    loadCurrentLanguage(); // Load language settings
    promptInput.focus();
  </script>
</body>
</html>
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { TauriAssistantRuntimeClient } from './services/runtime';
import './index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App runtimeClient={new TauriAssistantRuntimeClient()} />
  </React.StrictMode>,
);

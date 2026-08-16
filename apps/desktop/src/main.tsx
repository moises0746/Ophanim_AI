import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { resolveRuntimeClient } from './services/runtime';
import './index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App runtimeClient={resolveRuntimeClient()} />
  </React.StrictMode>,
);

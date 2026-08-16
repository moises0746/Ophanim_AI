import axe from 'axe-core';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../App';
import { ContextPanel } from '../features/assistant/ContextPanel';
import {
  OphanimAssistantVisual,
  assistantStatePresentation,
} from '../features/assistant/OphanimAssistantVisual';
import type { AssistantRuntimeClient } from '../services/runtime';
import type { AssistantSemanticState } from '../types/events';

const states = Object.keys(assistantStatePresentation) as AssistantSemanticState[];

afterEach(() => cleanup());
beforeEach(() => {
  window.location.hash = '#/';
});

function runtimeClient(): AssistantRuntimeClient {
  return {
    getConfig: vi.fn(async () => ({ configured: true, coreBaseUrl: 'http://127.0.0.1:8000', workspaceId: 'workspace-1' })),
    listModels: vi.fn(async () => [{
      provider: 'lm_studio' as const,
      model_id: 'local-model',
      display_name: 'LM Studio Local',
      context_window: 8192,
      capabilities: ['text'],
      is_local: true,
    }]),
    sendChat: vi.fn(async () => ({
      correlation_id: 'corr-1',
      content: 'Bounded response from Core.',
      provider: 'lm_studio' as const,
      model_id: 'local-model',
      finish_reason: 'stop',
      usage: { prompt_tokens: 4, completion_tokens: 5, total_tokens: 9 },
      latency_ms: 20,
    })),
    connectEvents: vi.fn(async (_workspaceId, handlers) => {
      handlers.onConnectionChange?.(true);
      return () => handlers.onConnectionChange?.(false);
    }),
  };
}

describe('Ophanim Desktop experience', () => {
  it('maps every canonical Assistant state to a semantic visual and text fallback', () => {
    for (const state of states) {
      const { unmount } = render(<OphanimAssistantVisual state={state} statusText="State test" />);
      const status = screen.getByRole('status');
      expect(status).toHaveAttribute('data-assistant-state', state);
      expect(status).toHaveAccessibleName(new RegExp(assistantStatePresentation[state].label, 'i'));
      unmount();
    }
    expect(states).toHaveLength(12);
  });

  it('renders the Assistant as the default route with truthful offline states', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
    expect(screen.getAllByText(/browser preview: the authenticated core runtime is not connected/i)).toHaveLength(2);
    expect(screen.getByRole('textbox', { name: /message ophanim/i })).toBeDisabled();
    expect(screen.getByText(/no activity yet/i)).toBeInTheDocument();
  });

  it('navigates the requested route shell and shows an honest models empty state', async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole('link', { name: /models & runtimes/i }));
    expect(await screen.findByRole('heading', { name: /model routing/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /no models available/i })).toBeInTheDocument();
  });

  it('sends a typed chat through the runtime and renders the real response', async () => {
    const client = runtimeClient();
    const user = userEvent.setup();
    render(<App runtimeClient={client} />);
    const composer = await screen.findByRole('textbox', { name: /message ophanim/i });
    await waitFor(() => expect(composer).toBeEnabled());
    await user.type(composer, 'Hello Ophanim');
    await user.click(screen.getByRole('button', { name: /^send$/i }));
    expect(await screen.findByText('Bounded response from Core.')).toBeInTheDocument();
    expect(client.sendChat).toHaveBeenCalledWith(expect.objectContaining({
      provider: 'lm_studio',
      modelId: 'local-model',
      privacyMode: 'LOCAL_ONLY',
    }));
  });

  it('switches contextual tabs without inventing sources or tool activity', async () => {
    const user = userEvent.setup();
    render(<ContextPanel events={[]} citations={[]} />);
    await user.click(screen.getByRole('tab', { name: /sources/i }));
    expect(screen.getByText(/no verified sources/i)).toBeInTheDocument();
    await user.click(screen.getByRole('tab', { name: /tools/i }));
    expect(screen.getByText(/no tool calls/i)).toBeInTheDocument();
  });

  it('has no detectable automated accessibility violations in the default workspace', async () => {
    const { container } = render(<App />);
    const result = await axe.run(container, {
      rules: { 'color-contrast': { enabled: false } },
    });
    expect(result.violations).toEqual([]);
  });
});

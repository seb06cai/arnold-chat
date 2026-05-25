import { POST } from './route';
import { NextRequest } from 'next/server';

jest.mock('livekit-server-sdk', () => ({
  AccessToken: jest.fn().mockImplementation(() => ({
    addGrant: jest.fn(),
    toJwt: jest.fn().mockResolvedValue('mock-jwt'),
  })),
}));

const req = (body: object) =>
  new NextRequest('http://localhost/api/token', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  });

describe('POST /api/token', () => {
  beforeEach(() => {
    process.env.LIVEKIT_API_KEY = 'key';
    process.env.LIVEKIT_API_SECRET = 'secret';
    process.env.LIVEKIT_URL = 'wss://test.livekit.cloud';
  });

  it('returns 201 with server_url and participant_token', async () => {
    const res = await POST(req({}));
    const data = await res.json();
    expect(res.status).toBe(201);
    expect(data.server_url).toBe('wss://test.livekit.cloud');
    expect(data.participant_token).toBe('mock-jwt');
  });

  it('accepts optional room_name and participant_name without error', async () => {
    const res = await POST(req({ room_name: 'gym', participant_name: 'Trainee' }));
    expect(res.status).toBe(201);
  });
});

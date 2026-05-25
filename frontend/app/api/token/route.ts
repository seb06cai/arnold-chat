import { RoomAgentDispatch, RoomConfiguration } from '@livekit/protocol';
import { AccessToken } from 'livekit-server-sdk';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  let body: { room_name?: string; participant_identity?: string; participant_name?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }

  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  const serverUrl = process.env.LIVEKIT_URL;

  if (!apiKey || !apiSecret || !serverUrl) {
    return NextResponse.json({ error: 'Server misconfigured' }, { status: 500 });
  }

  const roomName = body.room_name ?? `arnold-${Date.now()}`;
  const identity = body.participant_identity ?? `user-${Date.now()}`;

  const token = new AccessToken(apiKey, apiSecret, {
    identity,
    name: body.participant_name ?? 'Trainee',
    ttl: '30m',
  });

  token.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
  });

  token.roomConfig = new RoomConfiguration({
    agents: [new RoomAgentDispatch({ agentName: 'arnold-coach' })],
  });

  return NextResponse.json(
    { server_url: serverUrl, participant_token: await token.toJwt() },
    { status: 201 },
  );
}

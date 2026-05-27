import Pusher from "pusher-js"

let pusherClient: Pusher | null = null

export function getPusherClient() {
  if (pusherClient) {
    return pusherClient
  }

  const key = process.env.NEXT_PUBLIC_PUSHER_KEY
  const cluster = process.env.NEXT_PUBLIC_PUSHER_CLUSTER

  if (!key || !cluster) {
    throw new Error(
      "Missing Pusher client configuration. Set NEXT_PUBLIC_PUSHER_KEY and NEXT_PUBLIC_PUSHER_CLUSTER.",
    )
  }

  pusherClient = new Pusher(key, {
    cluster,
  })

  return pusherClient
}

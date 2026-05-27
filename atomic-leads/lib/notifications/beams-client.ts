import * as PusherPushNotifications from "@pusher/push-notifications-web"

let beamsClient: PusherPushNotifications.Client | null = null

export async function initBeamsClient() {
  if (beamsClient) {
    return beamsClient
  }

  const instanceId = process.env.NEXT_PUBLIC_PUSHER_BEAMS_INSTANCE_ID

  if (!instanceId) {
    throw new Error(
      "Missing Beams configuration. Set NEXT_PUBLIC_PUSHER_BEAMS_INSTANCE_ID.",
    )
  }

  beamsClient = new PusherPushNotifications.Client({
    instanceId,
  })

  await beamsClient.start()

  return beamsClient
}

export enum RunProfile {
  OFFLINE = 'OFFLINE',
  ONLINE = 'ONLINE',
}

export type NetworkPolicy = {
  allowInternet: boolean
  allowLoopback: boolean
}

export type FeatureGate = {
  canCheckUpdate: boolean
  offlineReason: string
}

export const OFFLINE_REASON = '当前为离线便携模式，该功能需要联网，暂不可用'

export function getDefaultNetworkPolicy(profile: RunProfile): NetworkPolicy {
  if (profile === RunProfile.ONLINE) {
    return { allowInternet: true, allowLoopback: true }
  }
  return { allowInternet: false, allowLoopback: true }
}

export function getDefaultFeatureGate(profile: RunProfile): FeatureGate {
  const offline = profile === RunProfile.OFFLINE
  return {
    canCheckUpdate: !offline,
    offlineReason: OFFLINE_REASON,
  }
}

// EC2 每天排程關機的時段（台灣時間）。要和 infra/terraform/modules/backend 的
// ec2_stop_schedule / ec2_start_schedule 一致，改其中一邊時另一邊也要改。
export const SERVER_REST_START_HOUR = 2
export const SERVER_REST_END_HOUR = 16
const SERVER_TIME_ZONE = 'Asia/Taipei'

export function isServerResting(now: Date = new Date()): boolean {
  const hour = Number(
    new Intl.DateTimeFormat('en-US', {
      timeZone: SERVER_TIME_ZONE,
      hour: 'numeric',
      hourCycle: 'h23',
    }).format(now),
  )
  return hour >= SERVER_REST_START_HOUR && hour < SERVER_REST_END_HOUR
}

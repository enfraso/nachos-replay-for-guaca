/**
 * Nachos Replay - Pinia Store Index
 */
import { createPinia } from 'pinia'

export const pinia = createPinia()

export { useAuthStore } from './auth'
export { useReplaysStore } from './replays'
export { useStatsStore } from './stats'

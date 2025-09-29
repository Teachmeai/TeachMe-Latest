import { useState, useEffect, useCallback } from 'react'

export type TabValue = string

export function useTabState(key: string, defaultValue: TabValue) {
  const [tab, setTab] = useState<TabValue>(defaultValue)

  // Load tab state from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(key)
      if (saved) {
        setTab(saved)
      }
    } catch (error) {
      console.warn('Failed to load tab state from localStorage:', error)
    }
  }, [key])

  // Save tab state to localStorage when it changes
  const setTabWithStorage = useCallback((newTab: TabValue) => {
    setTab(newTab)
    try {
      localStorage.setItem(key, newTab)
    } catch (error) {
      console.warn('Failed to save tab state to localStorage:', error)
    }
  }, [key])

  return [tab, setTabWithStorage] as const
}

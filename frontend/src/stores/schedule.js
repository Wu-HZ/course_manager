import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getActiveSchedule, getScheduleResults } from '../api/scheduler'

export const useScheduleStore = defineStore('schedule', () => {
  const activeResult = ref(null)
  const results = ref([])

  const fetchActive = async () => {
    try {
      activeResult.value = await getActiveSchedule()
    } catch (e) {
      activeResult.value = null
    }
  }

  const fetchResults = async () => {
    results.value = await getScheduleResults()
  }

  return { activeResult, results, fetchActive, fetchResults }
})

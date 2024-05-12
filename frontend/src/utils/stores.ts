import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type globStore = {
    header: any
    setHeader: (h:any) => void,
    loading: boolean,
    setLoader: (l:boolean) => void,
    showLoader: () => void, 
    hideLoader: () => void,
}

type tokenStore = {
    loginToken: any
    setToken: (t:any) => void
}

export const useGlobalStore = create<globStore>()((set) => ({
  header: null,
  loading: false,
  setHeader: (header) => set(() => ({ header })),
  setLoader: (loading) => set(() => ({ loading })),
  showLoader: () => set(() => ({ loading: true })),
  hideLoader: () => set(() => ({ loading: false })),
}))

export const useTokenStore = create<tokenStore>()(
    persist(
      (set) => ({
        loginToken: null,
        setToken: (tk) => set(() => ({ loginToken:tk })),
      }),
      {
        name: 'token-storage'
      },
    ),
  )
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
        name: 'tokens'
      },
    ),
  )

type settingsStore = {
    tablePageSize: number
    refreshInterval: number
    statusRefreshInterval: number,
    setStatusRefreshInterval: (sri:number) => void
    setTablePageSize: (psr:number) => void
    setRefreshInterval: (ri:number) => void
}

export const useSettingsStore = create<settingsStore>()(
  persist(
    (set) => ({
      tablePageSize: 30,
      refreshInterval: 5000,
      setTablePageSize: (psr) => set(() => ({ tablePageSize:psr })),
      setRefreshInterval: (ri) => set(() => ({ refreshInterval:ri })),
      statusRefreshInterval: 3000,
      setStatusRefreshInterval: (sri) => set(() => ({ statusRefreshInterval:sri })),
    }),
    {
      name: 'settings'
    },
  ),
)


export const useConnectFailTimeStore = create<{
    connectionFails: number,
    maxFails: number,
    failed: boolean,
    setConnectionFails: (cf:number) => void
    reset: () => void
}>()(
    (set, get) => ({
        connectionFails: 0,
        maxFails: 3,
        failed: false,
        setConnectionFails: (cf:number) => set(() => ({ connectionFails:cf, failed:cf >= get().maxFails})),
        reset: () => set(() => ({ connectionFails:0, failed:false })),
    })
)
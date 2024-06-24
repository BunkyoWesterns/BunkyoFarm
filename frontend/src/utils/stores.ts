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
    setPageLayout: (psr:number, ps:number) => boolean
    setRefreshInterval: (ri:number) => void
}

export const useSettingsStore = create<settingsStore>()(
  persist(
    (set) => ({
      tablePageSize: 30,
      refreshInterval: 5000,
      setPageLayout: (psr, ps) => {
        if (psr >= ps && psr >= 1 && psr%ps === 0){
          set(() => ({ pageSizeRequest:psr, tablePageSize:ps }))
          return true;
        }else{
          return false;
        }
      },
      setRefreshInterval: (ri) => set(() => ({ refreshInterval:ri })),
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
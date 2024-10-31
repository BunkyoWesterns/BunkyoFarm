import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type ErrorMsg = {
  title: string,
  message: string,
  color: string,
}

type globStore = {
    header: any
    loading: boolean,
    errorMessage: ErrorMsg|null,
    setHeader: (h:any) => void,
    setErrorMessage: (e:ErrorMsg|null) => void,
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
  errorMessage: null,
  setHeader: (header) => set(() => ({ header })),
  setLoader: (loading) => set(() => ({ loading })),
  showLoader: () => set(() => ({ loading: true })),
  hideLoader: () => set(() => ({ loading: false })),
  setErrorMessage: (errorMessage) => set(() => ({ errorMessage })),
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
    setTablePageSize: (psr:number) => void
}

export const useSettingsStore = create<settingsStore>()(
  persist(
    (set) => ({
      tablePageSize: 30,
      setTablePageSize: (psr) => set(() => ({ tablePageSize:psr })),
    }),
    {
      name: 'settings'
    },
  ),
)

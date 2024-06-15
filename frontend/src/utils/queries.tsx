import { useQuery } from "@tanstack/react-query";
import { getRequest } from "@/utils/net";
import { paths } from "./backend_types";
import { useSettingsStore } from "./stores";

export const statusQuery = () => useQuery({
    queryKey: ["status"],
    queryFn: async () => await getRequest("/status") as paths["/api/status"]["get"]["responses"][200]["content"]["application/json"],
    refetchInterval: 1000
})

export const flagsQuery = (page:number) => {
    const [pageSizeRequest, refreshDataTime] = useSettingsStore((state) => [state.pageSizeRequest, state.refreshInterval])
    return useQuery({
        queryKey: ["flags", pageSizeRequest, page],
        queryFn: async () => await getRequest("/flags",{
            params: {
                page: page,
                size: pageSizeRequest
            }
        }) as paths["/api/flags"]["get"]["responses"][200]["content"]["application/json"],
        refetchInterval: refreshDataTime
    })
}

export const flagsStatsQuery = () => {
    const refreshDataTime = useSettingsStore((state) => state.refreshInterval)
    return useQuery({
        queryKey: ["flags-status"],
        queryFn: async () => await getRequest("/flags/stats") as paths["/api/flags/stats"]["get"]["responses"][200]["content"]["application/json"],
        refetchInterval: refreshDataTime
    })
}
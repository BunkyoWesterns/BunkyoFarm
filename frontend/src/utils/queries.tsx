import { useQuery } from "@tanstack/react-query";
import { getRequest } from "@/utils/net";
import { paths } from "./backend_types";

//Example
export const boardsQuery = () => useQuery({
    queryKey: ["textes"],
    queryFn: async () => await getRequest("/textes") as string[]
})

export const statusQuery = () => useQuery({
    queryKey: ["status"],
    queryFn: async () => await getRequest("/status") as paths["/api/status"]["get"]["responses"][200]["content"]["application/json"],
    staleTime: 1000
})

export const flagsQuery = (page:number, pageSize:number = 500) => useQuery({
    queryKey: ["flags", pageSize, page],
    queryFn: async () => await getRequest("/flags",{
        params: {
            page: page,
            size: pageSize
        }
    
    }) as paths["/api/flags"]["get"]["responses"][200]["content"]["application/json"]
})

export const flagsStatsQuery = () => useQuery({
    queryKey: ["flags-status"],
    queryFn: async () => await getRequest("/flags/stats") as paths["/api/flags/stats"]["get"]["responses"][200]["content"]["application/json"]
})

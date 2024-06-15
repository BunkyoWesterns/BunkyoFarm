import { useQuery } from "@tanstack/react-query";
import { getRequest } from "@/utils/net";
import { paths } from "./backend_types";
import { useConnectFailTimeStore, useSettingsStore } from "./stores";
import { useMemo } from "react";

export const statusQuery = () => {
    const failTimes = 3
    const [failures, setFailures] = useConnectFailTimeStore((state) => [state.connectionFails, state.setConnectionFails])
    return useQuery({
        queryKey: ["status"],
        queryFn: async () => await getRequest("/status") as paths["/api/status"]["get"]["responses"][200]["content"]["application/json"],
        refetchInterval: (failures < failTimes)?1000:undefined,
        retry(failureCount, _error) {
            setFailures(failureCount)
            return (failureCount < failTimes)
        },
    })
}

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

export const exploitsQuery = () => {
    const refreshDataTime = useSettingsStore((state) => state.refreshInterval)
    return useQuery({
        queryKey: ["exploits"],
        queryFn: async () => await getRequest("/exploits") as paths["/api/exploits"]["get"]["responses"][200]["content"]["application/json"],
        refetchInterval: refreshDataTime
    })
}

export const flagsStatsQuery = () => {
    const refreshDataTime = useSettingsStore((state) => state.refreshInterval)
    return useQuery({
        queryKey: ["flags", "stats"],
        queryFn: async () => await getRequest("/flags/stats") as paths["/api/flags/stats"]["get"]["responses"][200]["content"]["application/json"],
        refetchInterval: refreshDataTime
    })
}

export const useServiceMapping = () => {
    const status = statusQuery()
    return useMemo(() => {
        const services = status.data?.services?.map((service) => ({[service.id]: service}))
        if (services == null || services.length == 0) return {}
        return services.reduce((acc, val) => ({...acc, ...val}), {})
    }, [status.isFetching])
}

export const useTeamMapping = () => {
    const status = statusQuery()
    return useMemo(() => {
        const teams = status.data?.teams?.map((team) => ({[team.id]: team}))
        if (teams == null || teams.length == 0) return {}
        return teams.reduce((acc, val) => ({...acc, ...val}), {})
    }, [status.isFetching])
}

export const useExploitMapping = () => {
    const exploits = exploitsQuery()
    return useMemo(() => {
        const exp = exploits.data?.map((exploit) => ({[exploit.id]: exploit}))
        if (exp == null || exp.length == 0) return {}
        return exp.reduce((acc, val) => ({...acc, ...val}), {})
    }, [exploits.isFetching])
}

export const useServiceSolver = () => {
    const services = useServiceMapping()
    return (id?:string|null) => {
        if (id == null) return "Unknown"
        const service = services[id]
        if (service == null) return `Service ${id}`
        return service.name
    
    }
}

export const useTeamSolver = () => {
    const teams = useTeamMapping()
    return (id?:number|null) => {
        if (id == null) return "Unknown"
        const team = teams[id]
        if (team == null) return `Team ${id}`
        if (team.name != null) return team.name
        if (team.short_name != null) return team.short_name
        return `Team ${team.host}`
    }
}

export const useExploitSolver = () => {
    const exploits = useExploitMapping()
    return (id?:string|null) => {
        if (id == null) return "Unknown"
        const exploit = exploits[id]
        if (exploit == null) return `Exploit ${id}`
        return exploit.name
    }
}

export const useExtendedExploitSolver = () => {
    const exploits = useExploitMapping()
    const services = useServiceMapping()
    return (id?:string|null) => {
        if (id == null) return "Unknown"
        const exploit = exploits[id]
        if (exploit == null) return `Exploit ${id}`
        return <>
            <b>{services[exploit.service]?.name??`Service ${exploit.service}`}</b> ({exploit.name})
        </>
    }
}


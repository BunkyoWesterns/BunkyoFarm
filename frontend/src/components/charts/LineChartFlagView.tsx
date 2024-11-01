import { hashedColor } from "@/utils"
import { clientsQuery, exploitsQuery, statsQuery, statusQuery } from "@/utils/queries"
import { getDateSmallFormatted } from "@/utils/time"
import { FlagStatuses } from "@/utils/types"
import { AreaChart, ChartData } from "@mantine/charts"
import { Box, Divider, Space } from "@mantine/core"
import { useMemo } from "react"
import { FlagTypeControl, SeriesTypeChartControl, TypeLineChartControl } from "@/components/inputs/Controllers"
import { useLocalStorage } from "@mantine/hooks"

export type SeriesType = "services"|"clients"|"exploits"|"globals"
export type FlagStatusType = FlagStatuses|"tot"
export type LineChartType = "area"|"classic"

//This will be expanded in the future
export const LineChartFlagView = ({ seriesType, flagType, chartType, withControls }:{ seriesType?: SeriesType, flagType?:FlagStatusType, chartType?:LineChartType, withControls?:boolean }) => {
    const status = statusQuery()
    const exploits = exploitsQuery()
    const clients = clientsQuery()
    const base_secret = status.data?.server_id??"_"
    const [seriesTypeChart, setSeriesTypeChart] = useLocalStorage<SeriesType>({ key: "flagSeriesType", defaultValue:seriesType??"services"})
    const [flagStatusFilterChart, setFlagStatusFilterChart] = useLocalStorage<FlagStatusType>({ key: "flagStatusFilter", defaultValue:flagType??"ok"})
    const [flagTypeChart, setFlagTypeChart] = useLocalStorage<LineChartType>({ key: "flagTypeChart", defaultValue:chartType??"area"})

    const finalSeries = withControls?seriesTypeChart:(seriesType??"services")
    const finalFlagStatus = withControls?flagStatusFilterChart:(flagType??"ok")
    const finalChartType = withControls?flagTypeChart:(chartType??"area")

    const series = useMemo(() => {
        if (finalSeries == "services"){
            return [
                { name: "null", label: "Manual", color: "gray"},
                ...status.data?.services?.map((service) => ({ name: service.id, label: service.name, color: hashedColor(base_secret+service.id) }))??[]
            ]
        }
        if (finalSeries == "clients"){
            return [
                ...clients.data?.map((client) => ({ name: client.id, label: client.name??"Unknown", color: hashedColor(base_secret+client.id) }))??[]
            ].map((client) => ({ name: client.name, label: client.name == "manual"?"Manual":client.label, color: client.name == "manual"?"gray":client.color }))
        }
        if (finalSeries == "exploits"){
            return [
                { name: "null", label: "Manual", color: "gray"},
                ...exploits.data?.map((exploit) => ({ name: exploit.id, label: exploit.name, color: hashedColor(base_secret+exploit.id) }))??[]
            ]
        }
        if (finalSeries == "globals"){
            return [
                { name: "ok", label: "OK", color: "green"},
                { name: "timeout", label: "Timeout", color: "yellow"},
                { name: "invalid", label: "Invalid", color: "red"},
                { name: "wait", label: "Wait", color: "blue"}
            ].filter((flag) => flag.name == finalFlagStatus || finalFlagStatus == "tot")
        }
        return []
    }, [status.isFetching, finalSeries, exploits.isFetching, clients.isFetching, finalFlagStatus])
    const stats = statsQuery()
    const useTick = status.data?.config?.START_TIME != null
    const data = useMemo(() => {
        let initialSkip = true
        const res = stats.data?.ticks.map((tick) => {
            let result:{ date: string, [s:string]: string|number} = { date: useTick?"Tick #"+tick.tick.toString():getDateSmallFormatted(tick.start_time) }
            if (finalSeries == "globals"){
                if (tick.globals.flags.tot > 0 || !initialSkip){
                    initialSkip = false
                    result = {...result, ...tick.globals.flags }
                }
            }else if (finalSeries == "services"){
                const used_ids = Object.keys(tick.exploits).map((id) => {
                    const service_id = exploits.data?.find((exploit) => exploit.id == id)?.service
                    if (service_id == null) return
                    const oldValue = (!result[service_id] || typeof result[service_id] == "string")?0:result[service_id] as number
                    if (tick.exploits[id]?.flags[finalFlagStatus] == null && initialSkip) return service_id
                    initialSkip = false
                    result[service_id] = tick.exploits[id]?.flags[finalFlagStatus]??0 + oldValue
                    return service_id
                })
                if (!initialSkip){
                    status.data?.services?.map((service) => service.id).filter((id) => !used_ids.includes(id)).forEach((id) => {
                        result[id] = 0
                    })
                }
            }else{
                const used_ids = Object.keys(tick[finalSeries]).map((id) => {
                    if (tick[finalSeries][id]?.flags[finalFlagStatus] == null && initialSkip) return id
                    initialSkip = false
                    result[id] = tick[finalSeries][id]?.flags[finalFlagStatus]??0
                    return id
                })
                if (!initialSkip){
                    if (finalSeries == "clients"){
                        clients.data?.map((client) => client.id).filter((id) => !used_ids.includes(id)).forEach((id) => {
                            result[id] = 0
                        })
                    }else if (finalSeries == "exploits"){
                        exploits.data?.map((exploit) => exploit.id).filter((id) => !used_ids.includes(id)).forEach((id) => {
                            result[id] = 0
                        })
                    }
                }
            }
            return result
        })
        return res?.filter((item) => Object.keys(item).length > 1)??[]
    }, [stats.isFetching, finalSeries, finalFlagStatus, exploits.isFetching])

    return <Box style={{width:"100%", minHeight:300}}>
        <b>Flag chart</b>
        <Space h="md" />
        <Divider />
        <Space h="lg" />
        <Space h="md" />
        <AreaChart
            h={300}
            mih={300}
            miw={100}
            data={data as ChartData}
            dataKey="date"
            type={finalChartType == "area" ? "stacked": undefined}
            withLegend
            legendProps={{ verticalAlign: 'bottom', height: 50 }}
            series={series}
        />
        {withControls?<>
            <Space h="lg" />
            <Box className="center-flex" style={{width:"100%", flexWrap: "wrap" }}>
                
                <SeriesTypeChartControl value={seriesTypeChart} onChange={setSeriesTypeChart} />
                <Box visibleFrom="md" style={{flexGrow: 1}} />
                <Box hiddenFrom="md" style={{flexBasis: "100%", height: 20}} />
                <Box className="center-flex">
                    <TypeLineChartControl value={flagTypeChart} onChange={setFlagTypeChart} />
                    <Space w="lg" />
                    <FlagTypeControl value={flagStatusFilterChart} onChange={setFlagStatusFilterChart} />
                </Box>
            </Box>
        </>:null}
    </Box>

}
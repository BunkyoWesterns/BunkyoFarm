import { hashedColor } from "@/utils"
import { clientsQuery, exploitsQuery, flagsStatsQuery, statusQuery } from "@/utils/queries"
import { getDateSmallFormatted } from "@/utils/time"
import { FlagStatuses } from "@/utils/types"
import { AreaChart, ChartData, LineChart } from "@mantine/charts"
import { Box, Space } from "@mantine/core"
import { useMemo, useState } from "react"
import { FlagTypeControl, SeriesTypeChartControl, TypeLineChartControl } from "./Controllers"

export type SeriesType = "services"|"clients"|"exploits"|"globals"
export type FlagStatusType = FlagStatuses|"tot"
export type LineChartType = "area"|"classic"

//This will be expanded in the future
export const LineChartFlagView = ({ seriesType, flagType, chartType, withControls }:{ seriesType?: SeriesType, flagType?:FlagStatusType, chartType?:LineChartType, withControls?:boolean }) => {
    const status = statusQuery()
    const exploits = exploitsQuery()
    const clients = clientsQuery()
    const base_secret = status.data?.config?.SERVER_ID??"_"
    const [seriesTypeChart, setSeriesTypeChart] = useState<SeriesType>(seriesType??"services")
    const [flagStatusFilterChart, setFlagStatusFilterChart] = useState<FlagStatusType>(flagType??"tot")
    const [flagTypeChart, setFlagTypeChart] = useState<LineChartType>(chartType??"area")

    const finalSeries = withControls?seriesTypeChart:(seriesType??"services")
    const finalFlagStatus = withControls?flagStatusFilterChart:(flagType??"tot")
    const finalChartType = withControls?flagTypeChart:(chartType??"area")

    const series = useMemo(() => {
        if (seriesTypeChart == "services"){
            return [
                { name: "null", label: "Manual", color: "gray"},
                ...status.data?.services?.map((service) => ({ name: service.id, label: service.name, color: hashedColor(base_secret+service.id) }))??[]
            ]
        }
        if (seriesTypeChart == "clients"){
            return [
                ...clients.data?.map((client) => ({ name: client.id, label: client.name??"Unknown", color: hashedColor(base_secret+client.id) }))??[]
            ].map((client) => ({ name: client.name, label: client.name == "manual"?"Manual":client.label, color: client.name == "manual"?"gray":client.color }))
        }
        if (seriesTypeChart == "exploits"){
            return [
                { name: "null", label: "Manual", color: "gray"},
                ...exploits.data?.map((exploit) => ({ name: exploit.id, label: exploit.name, color: hashedColor(base_secret+exploit.id) }))??[]
            ]
        }
        if (seriesTypeChart == "globals"){
            return [
                { name: "ok", label: "OK", color: "green"},
                { name: "timeout", label: "Timeout", color: "red"},
                { name: "invalid", label: "Invalid", color: "yellow"},
                { name: "wait", label: "Wait", color: "blue"}
            ].filter((flag) => flag.name == flagStatusFilterChart || flagStatusFilterChart == "tot")
        }
        return []
    }, [status.isFetching])
    const stats = flagsStatsQuery()
    const useTick = status.data?.config?.START_TIME != null
    const data = useMemo(() => {
        const res = stats.data?.ticks.map((tick) => {
            let result:{ date: string, [s:string]: string|number} = { date: useTick?"Tick #"+tick.tick.toString():getDateSmallFormatted(tick.start_time) }
            if (finalSeries == "globals"){
                result = {...result, ...tick.globals.flags }
            }else{
                Object.keys(tick[finalSeries]).forEach((id) => {
                    result[id] = tick[finalSeries][id].flags[finalFlagStatus]??0
                })
            }
            return result
        })
        return res
    }, [stats.isFetching, finalSeries, finalFlagStatus, finalChartType])

    const ChartComponent = finalChartType == "area" ? AreaChart : LineChart

    return <>
        <Space h="lg" />
        <Space h="md" />
        <ChartComponent
            h={300}
            data={data as ChartData}
            dataKey="date"
            type="stacked"
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
    </>

}
import { hashedColor } from "@/utils"
import { flagsStatsQuery, statusQuery } from "@/utils/queries"
import { getDateSmallFormatted } from "@/utils/time"
import { AreaChart, ChartData } from "@mantine/charts"
import { Space, Title } from "@mantine/core"
import { useMemo } from "react"


//This will be expanded in the future
export const ChartView = () => {
    const status = statusQuery()
    const base_secret = status.data?.config?.SERVER_ID??"_"
    const series = useMemo(() => {
        return [
            { name: "null", label: "Manual", color: "gray"},
            ...status.data?.services?.map((service) => ({ name: service.id, label: service.name, color: hashedColor(base_secret+service.id) }))??[]
        ]
    }, [status.isFetching])
    const stats = flagsStatsQuery()
    const useTick = status.data?.config?.START_TIME != null
    const data = useMemo(() => {
        const res = stats.data?.ticks.map((tick) => {
            let result:{ date: string, [s:string]: string|number} = { date: useTick?"Tick #"+tick.tick.toString():getDateSmallFormatted(tick.start_time) }
            Object.keys(tick.services).forEach((service) => {
                result[service] = tick.services[service].flags.tot??0
            })
            return result
        })
        return res
    }, [stats.isFetching])
    return <>
        <Space h="lg" />
        <Title order={1}>Chart</Title>
        <Space h="xl" />
        <Space h="md" />
        <AreaChart
            h={300}
            data={data as ChartData}
            dataKey="date"
            type="stacked"
            withLegend
            legendProps={{ verticalAlign: 'bottom', height: 50 }}
            series={series}
        />
        [Charts will be more dynamic in the future]
    </>

}
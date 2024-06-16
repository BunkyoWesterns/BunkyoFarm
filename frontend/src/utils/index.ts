import { useEffect, useState } from "react";
import { flagsRequest, statusQuery } from "./queries";

export function stringToHash(string:string) {

    let hash = 0;

    if (string.length == 0) return hash;

    for (let i = 0; i < string.length; i++) {
        let char = string.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }

    return hash;
}

export const hashedColor = (string:string) => {
    return GRAPH_COLOR_PALETTE[Math.abs(stringToHash(string)) % GRAPH_COLOR_PALETTE.length]
}

export const GRAPH_COLOR_PALETTE = [
    "red", "pink", "grape", "violet", "indigo", "blue", "cyan", "teal", "green", "lime", "yellow", "orange"
]

export const useTimeOptions = (): [Date|null, number|null] => {
    const status = statusQuery()
    const [startTime, setStartTime] = useState<Date|null>(null)
    const tickTime = status.data?.config?.TICK_DURATION

    useEffect(() => {(async () => {
        if (status.data?.config?.START_TIME != null) setStartTime(new Date(status.data?.config?.START_TIME))
        else {
            const flags = await flagsRequest(1, 1, { reversed: true })
            if (flags.items.length > 0){
                const firstTime = flags.items[0].attack.start_time
                if (firstTime != null)
                    setStartTime(new Date(firstTime))
                else
                    setStartTime(null)
            }else{
                setStartTime(null)
            }
        }
    })()},[status.data?.config?.START_TIME])
    
    return (startTime && tickTime)?[startTime, tickTime]:[null, null]
}

export const useTickSelector = () => {
    const [startTime, tickTime] = useTimeOptions()
    return (startTime == null || tickTime == null)?null:
    (date: string|Date) => {
        if (typeof date === "string") date = new Date(date)
        return Math.floor((date.getTime()-startTime.getTime())/(tickTime*1000))+1
    }
}

export const useTickInfo = () => {
    const [startTime, tickTime] = useTimeOptions()
    return (startTime == null || tickTime == null)?null:
    (tick: number) => {
        return new Date(startTime.getTime() + (tick-1)*tickTime*1000)
    }
}

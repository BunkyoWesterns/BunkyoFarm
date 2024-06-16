import { components } from "./backend_types";


export type FlagStatuses = components["schemas"]["FlagStatus"]


export type FlagStat = {
    timeout: number,
    wait: number,
    invalid: number,
    ok: number,
    tot: number
}

export type AttackStat = {
    done: number,
    noflags: number,
    crashed: number,
    tot: number
}

export type GlobalStat = {
    flags: FlagStat,
    attacks: AttackStat
}

export type TickStat = {
    tick: number,
    start_time: string,
    end_time: string,
    globals: GlobalStat,
    exploits: {[s:string]: GlobalStat},
    services: {[s:string]: GlobalStat},
    teams: {[s:string]: GlobalStat},
    clients: {[s:string]: GlobalStat}
}

export type Stats = {
    ticks: TickStat[],
    globals: GlobalStat,
}
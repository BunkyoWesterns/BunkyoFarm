import { components } from "./backend_types";


export type FlagStatuses = components["schemas"]["FlagStatus"]
export type AttackStatuses = components["schemas"]["AttackExecutionStatus"]
export type AttackMode = components["schemas"]["AttackMode"]
export type SetupStatus = components["schemas"]["SetupStatus"]
export type Team = components["schemas"]["TeamDTO"]
export type AttackExecution = components["schemas"]["AttackExecutionDTO"]
export type AttackExecutionRestricted = components["schemas"]["FlagDTOAttackDetails"]
export type Clinet = components["schemas"]["ClientDTO"]
export type Service = components["schemas"]["ServiceDTO"]
export type Exploit = components["schemas"]["ExploitDTO"]
export type Language = components["schemas"]["Language"]
export const LanguageList = ["python", "java", "javascript", "typescript", "c#", "c++", "php", "r", "kotlin", "go", "ruby", "rust", "lua", "dart", "perl", "haskell", "other"]
export const KargsSubmitterList = ["int", "str", "float", "bool", "any"]
export type KargsSubmitter = "int"|"str"|"float"|"bool"|"any"

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
    exploits: {[s:string]: GlobalStat|undefined},
    teams: {[s:string]: GlobalStat|undefined},
    clients: {[s:string]: GlobalStat|undefined}
}

export type Stats = {
    ticks: TickStat[],
    globals: GlobalStat,
}



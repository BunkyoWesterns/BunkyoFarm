import { Box, SegmentedControl, Space, Tooltip } from "@mantine/core"
import { FlagStatusType, LineChartType, SeriesType } from "@/components/charts/LineChartFlagView"
import { AttackModeIcon, AttackStatusIcon, FlagStatusIcon } from "@/components/elements/StatusIcon";
import { FaChartArea } from "react-icons/fa";
import { FaChartLine } from "react-icons/fa6";
import { MdMiscellaneousServices } from "react-icons/md";
import { GoPersonFill } from "react-icons/go";
import { PiSwordBold } from "react-icons/pi";
import { IoFlagSharp } from "react-icons/io5";
import { AttackStatusType } from "@/components/charts/LineChartAttackView";
import { AttackMode } from "@/utils/types";

export const FlagTypeControl = ({ value, onChange }:{ value: FlagStatusType, onChange:(v:FlagStatusType) => void}) => {
    return <SegmentedControl data={[
            {
                label: <Box className="center-flex" h={25} w={25}><FlagStatusIcon status="tot" /></Box>,
                value: "tot",
            },
            {
                label: <Box className="center-flex" h={25} w={25}><FlagStatusIcon status="ok" /></Box>,
                value: "ok",
            },
            {
                label: <Box className="center-flex" h={25} w={25}><FlagStatusIcon status="timeout" /></Box>,
                value: "timeout",
            },
            {
                label: <Box className="center-flex" h={25} w={25}><FlagStatusIcon status="invalid" /></Box>,
                value: "invalid",
            },
            {
                label: <Box className="center-flex" h={25} w={25}><FlagStatusIcon status="wait" /></Box>,
                value: "wait",
            }
        ]}
        onChange={(v)=>{
            onChange(v as FlagStatusType)
        }}
        value={value}
    />
}

export const AttackTypeControl = ({ value, onChange }:{ value: AttackStatusType, onChange:(v:AttackStatusType) => void}) => {
    return <SegmentedControl data={[
            {
                label: <Box className="center-flex" h={25} w={25}><AttackStatusIcon status="tot" /></Box>,
                value: "tot",
            },
            {
                label: <Box className="center-flex" h={25} w={25}><AttackStatusIcon status="done" /></Box>,
                value: "done",
            },
            {
                label: <Box className="center-flex" h={25} w={25}><AttackStatusIcon status="noflags" /></Box>,
                value: "noflags",
            },
            {
                label: <Box className="center-flex" h={25} w={25}><AttackStatusIcon status="crashed" /></Box>,
                value: "crashed",
            }
        ]}
        onChange={(v)=>{
            onChange(v as AttackStatusType)
        }}
        value={value}
    />
}

export const TypeLineChartControl = ({ value, onChange }:{ value: LineChartType, onChange:(v:LineChartType) => void}) => {
    return <SegmentedControl data={[
            {
                label: <Tooltip label="Area chart" color="gray">
                    <Box className="center-flex" h={25} w={25}><FaChartArea size={20}/></Box>
                </Tooltip>,
                value: "area",
            },
            {
                label: <Tooltip label="Line chart" color="gray">
                    <Box className="center-flex" h={25} w={25}><FaChartLine size={20} /></Box>
                </Tooltip>,
                value: "classic",
            }
        ]}
        onChange={(v)=>{
            onChange(v as LineChartType)
        }}
        value={value}
        color="violet"
    />
}

export const SeriesTypeChartControl = ({ value, onChange }:{ value: SeriesType, onChange:(v:SeriesType) => void}) => {
    return <SegmentedControl data={[
            {
                label: <Box className="center-flex" h={25}>
                    <MdMiscellaneousServices size={20} />
                    <Space w="xs" />
                    Services
                </Box>,
                value: "services",
            },
            {
                label: <Box className="center-flex" h={25}>
                    <GoPersonFill size={20} />
                    <Space w="xs" />
                    Clients
                </Box>,
                value: "clients",
            },
            {
                label: <Box className="center-flex" h={25}>
                    <PiSwordBold size={20} />
                    <Space w="xs" />
                    Exploits
                </Box>,
                value: "exploits",
            },
            {
                label: <Box className="center-flex" h={25}>
                    <IoFlagSharp size={20} />
                    <Space w="xs" />
                    General
                </Box>,
                value: "globals",
            }
        ]}
        onChange={(v)=>{
            onChange(v as SeriesType)
        }}
        color={
            value == "services" ? "blue" :
            value == "clients" ? "green" :
            value == "exploits" ? "red" :
            "orange"
        }
        value={value}
    />
}

export const AttackModeControl = ({ value, onChange }:{ value: AttackMode, onChange:(v:AttackMode) => void}) => {
    return <SegmentedControl data={[
            {
                label: <Box className="center-flex">Tick delay<Space w="xs" /><Box className="center-flex" h={25} w={25}><AttackModeIcon status="tick-delay" /></Box></Box>,
                value: "tick-delay",
            },
            {
                label: <Box className="center-flex">Loop attack<Space w="xs" /><Box className="center-flex" h={25} w={25}><AttackModeIcon status="loop-delay" /></Box></Box>,
                value: "loop-delay",
            },
            {
                label: <Box className="center-flex">Tick time<Space w="xs" /><Box className="center-flex" h={25} w={25}><AttackModeIcon status="wait-for-time-tick" /></Box></Box>,
                value: "wait-for-time-tick",
            }
        ]}
        onChange={(v)=>{
            onChange(v as AttackMode)
        }}
        color={
            value == "loop-delay" ? "cyan" :
            value == "tick-delay" ? "#CD5C5C" :
            value == "wait-for-time-tick" ? "#DAA06D" :
            "orange"
        }
        value={value}
    />
}

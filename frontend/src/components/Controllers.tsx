import { Box, SegmentedControl, Space, Tooltip } from "@mantine/core"
import { FlagStatusType, LineChartType, SeriesType } from "./LineChartFlagView"
import { StatusIcon } from "./StatusIcon";
import { FaChartArea } from "react-icons/fa";
import { FaChartLine } from "react-icons/fa6";
import { MdMiscellaneousServices } from "react-icons/md";
import { GoPersonFill } from "react-icons/go";
import { PiSwordBold } from "react-icons/pi";
import { IoFlagSharp } from "react-icons/io5";

export const FlagTypeControl = ({ value, onChange }:{ value: FlagStatusType, onChange:(v:FlagStatusType) => void}) => {
    return <SegmentedControl data={[
            {
                label: <Box className="center-flex" h={25} w={25}><StatusIcon status="tot" /></Box>,
                value: "tot",
            },
            {
                label: <Box className="center-flex" h={25} w={25}><StatusIcon status="ok" /></Box>,
                value: "ok",
            },
            {
                label: <Box className="center-flex" h={25} w={25}><StatusIcon status="timeout" /></Box>,
                value: "timeout",
            },
            {
                label: <Box className="center-flex" h={25} w={25}><StatusIcon status="invalid" /></Box>,
                value: "invalid",
            },
            {
                label: <Box className="center-flex" h={25} w={25}><StatusIcon status="wait" /></Box>,
                value: "wait",
            }
        ]}
        onChange={(v)=>{
            onChange(v as FlagStatusType)
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

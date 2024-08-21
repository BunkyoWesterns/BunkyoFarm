import { FaFlag } from "react-icons/fa";
import { ImCross } from "react-icons/im";
import { MdTimerOff } from "react-icons/md";
import { FaUpload } from "react-icons/fa";
import { ActionIcon, MantineColor, MantineStyleProp, Tooltip } from "@mantine/core";
import { FlagStatusType } from "@/components/LineChartFlagView";
import { FaAsterisk } from "react-icons/fa";
import { AttackStatusType } from "./LineChartAttackView";
import { FaSkull } from "react-icons/fa6";
import { TbFlagOff } from "react-icons/tb";
import { AttackMode } from "@/utils/types";
import { TiArrowLoop } from "react-icons/ti";
import { LuTimerReset } from "react-icons/lu";
import { RiTimerFlashFill } from "react-icons/ri";
import { FaCheck } from "react-icons/fa";
import { RiEdit2Fill } from "react-icons/ri";

export const FlagStatusIcon = (props: {status:FlagStatusType, disableTooltip?:boolean}) => {
    
    let icon_info: {color: MantineColor, icon: JSX.Element, label: string} = {color: "black", icon: <></>, label: ""}

    switch (props.status) {
        case "ok":
            icon_info = {color: "LimeGreen", icon: <FaFlag size={20} />, label: "Flag has been submitted successfully"}
            break
        case "invalid":
            icon_info = { color: "red", icon: <ImCross size={20} />, label: "Flag has been submitted but is invalid"}
            break
        case "timeout":
            icon_info = { color: "orange", icon: <MdTimerOff size={25} />, label: "Flag is too old"}
            break
        case "wait":
            icon_info = { color: "DeepSkyBlue", icon: <FaUpload size={20} />, label: "Flag is pending for submission..." }
            break
        case "tot":
            icon_info = { color: "white", icon: <FaAsterisk size={20} />, label: "All flags"}
            break
    }
    if (props.disableTooltip)
        return <span
            style={{color: icon_info.color, textAlign: "center"}}
            className="center-flex"
        >{icon_info.icon}</span>
    else
        return <Tooltip color={icon_info.color!="white"?icon_info.color:"gray"} label={icon_info.label}>
            <span
                style={{color: icon_info.color, textAlign: "center"}}
                className="center-flex"
            >{icon_info.icon}</span>
        </Tooltip>
}

export const attackStatusTable = {
    done: {
        name: "Done",
        color: "LimeGreen",
        icon: FaFlag,
        label: "Attack has been executed successfully"
    },
    crashed: {
        name: "Crashed",
        color: "red",
        icon: FaSkull,
        label: "Attack has crashed"
    },
    noflags: {
        name: "No Flags",
        color: "orange",
        icon: TbFlagOff,
        label: "Attack has no flags"
    },
    tot: {
        name: "All",
        color: "white",
        icon: FaAsterisk,
        label: "All attacks"
    }
}

export const AttackStatusIcon = (props: {status:AttackStatusType, disableTooltip?:boolean}) => {
    
    let icon_info = attackStatusTable[props.status]
    if (props.disableTooltip)
        return <span
            style={{color: icon_info.color, textAlign: "center"}}
            className="center-flex"
        >{<icon_info.icon size={20} />}</span>
    else
        return <Tooltip color={icon_info.color!="white"?icon_info.color:"gray"} label={icon_info.label}>
            <span
                style={{color: icon_info.color, textAlign: "center"}}
                className="center-flex"
            >{<icon_info.icon size={20} />}</span>
        </Tooltip>
}

export const AttackModeIcon = (props: {status:AttackMode, disableTooltip?:boolean}) => {
    
    let icon_info: {color: MantineColor, icon: JSX.Element, label: string} = {color: "black", icon: <></>, label: ""}

    switch (props.status) {
        case "loop-delay":
            icon_info = {color: "cyan", icon: <TiArrowLoop size={30} />, label: "Wait for loop delay and run the attacks"}
            break
        case "tick-delay":
            icon_info = { color: "#B22222", icon: <LuTimerReset size={25} />, label: "Wait for a delay equivalent to the tick time and run the attacks"}
            break
        case "wait-for-time-tick":
            icon_info = { color: "yellow", icon: <RiTimerFlashFill size={25} />, label: "Run syncronized at the tick start by the start time of the competition"}
            break
    }

    if (props.disableTooltip)
        return <span
            style={{color: icon_info.color, textAlign: "center"}}
            className="center-flex"
        >{icon_info.icon}</span>
    else
        return <Tooltip color={icon_info.color!="white"?icon_info.color:"gray"} label={icon_info.label}>
            <span
                style={{color: icon_info.color, textAlign: "center"}}
                className="center-flex"
            >{icon_info.icon}</span>
        </Tooltip>
}

export const CancelActionButton = ({ disabled, onClick, style }: { disabled?: boolean, onClick: ()=>void, style?:MantineStyleProp}) => {
    return <ActionIcon
        onClick={onClick}
        disabled={disabled??false}
        color="red"
        style={{marginTop: 25, marginLeft: 10, ...(style??{})}}
        h={35}
        w={35}
    >
        <ImCross size={15}/>
    </ActionIcon>
}

export const EnableActionButton = ({ disabled, onClick, style }: { disabled?: boolean, onClick: ()=>void, style?:MantineStyleProp}) => {
    return <ActionIcon
        onClick={onClick}
        disabled={disabled??false}
        color="lime"
        style={{marginTop: 25, marginLeft: 10, ...(style??{})}}
        h={35}
        w={35}
    >
        <FaCheck size={15}/>
    </ActionIcon>
}

export const EditActionButton = ({ disabled, onClick, style }: { disabled?: boolean, onClick: ()=>void, style?:MantineStyleProp}) => {
    return <ActionIcon
        onClick={onClick}
        disabled={disabled??false}
        color="orange"
        style={{marginTop: 25, marginLeft: 10, ...(style??{})}}
        h={35}
        w={35}
    >
        <RiEdit2Fill size={20}/>
    </ActionIcon>
}
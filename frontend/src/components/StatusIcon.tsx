import { FaFlag } from "react-icons/fa";
import { ImCross } from "react-icons/im";
import { MdTimerOff } from "react-icons/md";
import { FaUpload } from "react-icons/fa";
import { Tooltip } from "@mantine/core";
import { FlagStatusType } from "@/components/LineChartFlagView";
import { FaAsterisk } from "react-icons/fa";
import { AttackStatusType } from "./LineChartAttackView";
import { FaSkull } from "react-icons/fa6";
import { TbFlagOff } from "react-icons/tb";

export const FlagStatusIcon = (props: {status:FlagStatusType, disableTooltip?:boolean}) => {
    
    let icon_info: {color: string, icon: JSX.Element, label: string} = {color: "black", icon: <></>, label: ""}

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

export const AttackStatusIcon = (props: {status:AttackStatusType, disableTooltip?:boolean}) => {
    
    let icon_info: {color: string, icon: JSX.Element, label: string} = {color: "black", icon: <></>, label: ""}

    switch (props.status) {
        case "done":
            icon_info = {color: "LimeGreen", icon: <FaFlag size={20} />, label: "Attack has been executed successfully"}
            break
        case "crashed":
            icon_info = { color: "red", icon: <FaSkull size={20} />, label: "Attack has crashed"}
            break
        case "noflags":
            icon_info = { color: "orange", icon: <TbFlagOff size={25} />, label: "Attack has no flags"}
            break
        case "tot":
            icon_info = { color: "white", icon: <FaAsterisk size={20} />, label: "All attacks"}
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
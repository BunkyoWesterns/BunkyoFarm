import { FaFlag } from "react-icons/fa";
import { ImCross } from "react-icons/im";
import { MdTimerOff } from "react-icons/md";
import { FaUpload } from "react-icons/fa";
import { Tooltip } from "@mantine/core";
import { FlagStatusType } from "@/components/LineChartFlagView";
import { FaAsterisk } from "react-icons/fa";

export const StatusIcon = (props: {status:FlagStatusType}) => {
    
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

    return <Tooltip color={icon_info.color!="white"?icon_info.color:"gray"} label={icon_info.label}>
        <span
            style={{color: icon_info.color, textAlign: "center"}}
            className="center-flex"
        >{icon_info.icon}</span>
    </Tooltip>
}
import { FlagStatuses } from "@/utils/types";
import { FaFlag } from "react-icons/fa";
import { ImCross } from "react-icons/im";
import { MdTimerOff } from "react-icons/md";
import { FaUpload } from "react-icons/fa";
import { Tooltip } from "@mantine/core";

export const StatusIcon = (props: {status:FlagStatuses}) => {
    
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
    }

    return <Tooltip color={icon_info.color} label={icon_info.label}>
        <span
            style={{color: icon_info.color, textAlign: "center"}}
            className="center-flex"
        >{icon_info.icon}</span>
    </Tooltip>
}
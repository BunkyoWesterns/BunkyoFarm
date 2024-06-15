import { FlagStatuses } from "@/utils/types";
import { FaFlag } from "react-icons/fa";
import { ImCross } from "react-icons/im";
import { MdTimerOff } from "react-icons/md";
import { FaUpload } from "react-icons/fa";

export const StatusIcon = (props: {status:FlagStatuses}) => {
    
    switch (props.status) {
        case "ok":
            return <span style={{color: "LimeGreen", textAlign: "center"}} className="center-flex"><FaFlag size={20} /></span>
        case "invalid":
            return <span style={{color: "red", textAlign: "center"}} className="center-flex"><ImCross size={20} /></span>
        case "timeout":
            return <span style={{color: "orange", textAlign: "center"}} className="center-flex"><MdTimerOff size={25} /></span>
        case "wait":
            return <span style={{color: "DeepSkyBlue", textAlign: "center"}} className="center-flex"><FaUpload size={20} /></span>
    }
}
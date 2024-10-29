import { Button } from "@mantine/core"
import { forwardRef } from "react";
import { CgOptions } from "react-icons/cg";
import { FaCheck, FaEdit, FaTrash } from "react-icons/fa";
import { IoMdArrowRoundBack } from "react-icons/io"
import { IoLogOut } from "react-icons/io5"
import { MdAdd } from "react-icons/md";
import { FaWrench } from "react-icons/fa6";
import { FaDownload } from "react-icons/fa";

export const BackButton =  forwardRef<HTMLButtonElement, {onClick?:()=>void, disabled?: boolean}>(({ onClick, disabled }, ref) => {
    return <Button ref={ref} color='cyan' size="compact-xs" radius={10} h={35} w={35} onClick={onClick} disabled={disabled}>
        <IoMdArrowRoundBack size={25} />
    </Button>
})

export const LogoutButton =  forwardRef<HTMLButtonElement,{onClick?:()=>void, disabled?: boolean}>(({ onClick, disabled }, ref) => {
    return <Button color='red' ref={ref} size="compact-xs" radius={10} h={35} w={35} onClick={onClick} disabled={disabled}>
        <IoLogOut size={25} />
    </Button>
})

export const AddButton = forwardRef<HTMLButtonElement, {onClick?:()=>void, disabled?: boolean}>(({ onClick, disabled }, ref) => {
    return <Button ref={ref} color='orange' size="compact-xs" radius={10} h={35} w={35} onClick={onClick} disabled={disabled}>
        <MdAdd size={28} />
    </Button>
})

export const OptionButton = forwardRef<HTMLButtonElement, {onClick?:()=>void, disabled?: boolean}>(({ onClick, disabled }, ref) => {
    return <Button ref={ref} color='blue' size="compact-xs" radius={10} h={35} w={35} onClick={onClick} disabled={disabled}>
        <CgOptions size={25} />
    </Button>
})

export const EngineButton = forwardRef<HTMLButtonElement, {onClick?:()=>void, disabled?: boolean}>(({ onClick, disabled }, ref) => {
    return <Button ref={ref} color='yellow' size="compact-xs" radius={10} h={35} w={35} onClick={onClick} disabled={disabled}>
        <FaWrench size={20} />
    </Button>
})

export const DeleteButton = forwardRef<HTMLButtonElement, {onClick?:()=>void, disabled?: boolean}>(({ onClick, disabled }, ref) => {
    return <Button ref={ref} color='red' size="compact-xs" radius={10} h={35} w={35} onClick={onClick} disabled={disabled}>
        <FaTrash size={15} />
    </Button>
})

export const DownloadButton = forwardRef<HTMLButtonElement, {onClick?:()=>void, disabled?: boolean}>(({ onClick, disabled }, ref) => {
    return <Button ref={ref} color='grape' size="compact-xs" radius={10} h={35} w={35} onClick={onClick} disabled={disabled}>
        <FaDownload size={15} />
    </Button>
})

export const EditButton = forwardRef<HTMLButtonElement, {onClick?:()=>void, disabled?: boolean}>((props, ref) => {
    return <Button ref={ref} color='blue' size="compact-xs" radius={10} h={35} w={35} {...props}>
        <FaEdit size={15} />
    </Button>
})

export const DoneButton = forwardRef<HTMLButtonElement, {onClick?:()=>void, disabled?: boolean}>((props, ref) => {
    return <Button ref={ref} color='green' size="compact-xs" radius={10} h={35} w={35} {...props}>
        <FaCheck size={15} />
    </Button>
})
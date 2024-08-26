import { Button, Group, MantineSize, Modal, Space } from "@mantine/core"

export const YesOrNoModal = ({ open, onClose, onConfirm, message, title, size }:{ open:boolean, onClose?: ()=>void, onConfirm?:()=>void, message:any, title?:any, size?:MantineSize }) => {
    return <Modal opened={open} onClose={()=>onClose?.()} title={title??"Are you sure?"} centered size={size??"sm"}>
        {message}
        <Space h="xl" />
        <Group justify="flex-end">
            <Button color="red" onClick={()=>{
                onConfirm?.()
                onClose?.()
            }}>Yes</Button>
            <Button onClick={onClose}>No</Button>
        </Group>
    </Modal>
}
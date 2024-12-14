import { useQueryClient } from "@tanstack/react-query"
import { YesOrNoModal } from "./YesOrNoModal"
import { Title } from "@mantine/core"
import { deleteGroup } from "@/utils/queries"
import { notifications } from "@mantine/notifications"
import { AttackGroup } from "@/utils/types"


export const DeleteGroupModal = ({ onClose, group }:{ onClose: () => void, group?: AttackGroup }) => {
    const queryClient = useQueryClient()

    return <YesOrNoModal
        open={ group != null }
        onClose={onClose}
        title={<Title order={3}>Deleting an attack group</Title>}
        onConfirm={()=>{
            if (group == null){
                onClose?.()
                return
            }
            deleteGroup(group?.id).then(()=>{
                notifications.show({ title: "Group deleted", message: `The group ${group?.name} has been deleted successfully`, color: "green" })
                queryClient.invalidateQueries({ queryKey: ["groups"] })

            }).catch((err)=>{
                notifications.show({ title: "Error deleting the group", message: `An error occurred while deleting the group ${group?.name}: ${err.message}`, color: "red" })
            }).finally(()=>{ onClose() })
        }}
        size="xl"
        message={
        <>
            <span>Are you sure you want to delete the group <b>{group?.name}</b>?</span><br />
            <span style={{ color: "yellow" }}>This action will stop the group if it is running!</span>
        </>
    }/>
}
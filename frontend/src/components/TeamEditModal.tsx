import { addTeamList, deleteTeamList, editTeamList, statusQuery } from "@/utils/queries";
import { getDateFormatted } from "@/utils/time";
import { Team } from "@/utils/types";
import { Alert, Box, Modal, Space, Table, TextInput } from "@mantine/core"
import { useEffect, useMemo } from "react";
import { useImmer } from "use-immer";
import { AddButton, DeleteButton, DoneButton } from "./Buttons";
import { notifications } from "@mantine/notifications";
import { MdError } from "react-icons/md";
import { useGlobalStore } from "@/utils/stores";

type TeamMapping = {[key: string]: Team}

export const TeamEditModal = (props:{
    opened:boolean,
    close:()=>void
}) => {
    const [teamInput, setTeamInput] = useImmer<TeamMapping>({})
    const [deleteTeam, setDeleteTeam] = useImmer<string[]>([])
    const [addTeam, setAddTeam] = useImmer<string[]>([])
    const [error, setError] = useImmer<string|null>(null)
    const setLoading = useGlobalStore((store) => store.setLoader)

    const genNewKey = () => {
        let count = 1
        let key = `new-${count}`
        while (Object.keys(teamInput).includes(key)){
            count++
            key = `new-${count}`
        }
        return key
    }

    const status = statusQuery()
    const teams: TeamMapping  = (status.data?.teams??[]).reduce((acc, val) => ({...acc, [val.id.toString()]: val}), {})
    
    useEffect(()=>{
        if (status.data){
            setTeamInput(teams)
        }
    }, [status.isLoading])


    const finalTeams = useMemo<TeamMapping>(()=>{
        let res = { ...teams, ...teamInput }
        deleteTeam.forEach((key) => {
            delete res[key]
        })
        return res
    }, [teamInput, status.isFetching, deleteTeam])
    
    const deltaTeams = useMemo<TeamMapping>(()=>{
        let res:any = {}
        deleteTeam.forEach((key) => {
            if (!Object.keys(finalTeams).includes(key)){
                setDeleteTeam((draft) => {
                    draft = draft.filter((k) => deleteTeam.includes(k))
                })
            }
        })
        Object.keys(teams).forEach((key)=>{
            if (teams[key] !== finalTeams[key] && !deleteTeam.includes(key.toString())){
                res[key] = finalTeams[key]
            }
        })
        addTeam.forEach((key)=>{
            res[key] = finalTeams[key]
        })
        return res
    }, [finalTeams, status.isFetching, deleteTeam, teamInput, addTeam])

    const isEdited = Object.keys(deltaTeams).length > 0 || addTeam.length > 0 || deleteTeam.length > 0

    const reset = () => {
        setTeamInput({})
        setDeleteTeam([])
        setAddTeam([])
        setError(null)
    }

    useEffect(reset, [props.opened])

    const rows = Object.keys(finalTeams).sort((a, b) => {
        return a.startsWith("new")?-1:
        b.startsWith("new")?1:
        parseInt(a) - parseInt(b)
    }).map((key) => {
        const element = finalTeams[key]
        return <Table.Tr key={key}>
            <Table.Td>{element.id}</Table.Td>
            <Table.Td>
                <TextInput
                    value={element.name??""}
                    placeholder="Team Name"
                    onChange={(e) => {
                        setTeamInput((draft) => {
                            if (draft[key] == undefined) draft[key] = { ...finalTeams[key]}
                            draft[key].name = e.target?.value??""
                        })
                    }}
                />
            </Table.Td>
            <Table.Td>
                <TextInput
                    value={element.short_name??""}
                    placeholder="Short Name"
                    onChange={(e) => {
                        setTeamInput((draft) => {
                            if (draft[key] == undefined) draft[key] = { ...finalTeams[key]}
                            draft[key].short_name = e.target?.value??""
                        })
                    }}
                />
            </Table.Td>
            <Table.Td>
                <TextInput
                    value={element.host??""}
                    placeholder="Host"
                    onChange={(e) => {
                        setTeamInput((draft) => {
                            if (draft[key] == undefined) draft[key] = { ...finalTeams[key]}
                            draft[key].host = e.target?.value??""
                        })
                    }}
                />
            </Table.Td>
            <Table.Td>{getDateFormatted(element.created_at)}</Table.Td>
            <Table.Td>
                <DeleteButton
                    onClick={()=>{
                        if (key.startsWith("new")){
                            setAddTeam((draft) => {
                                return draft.filter((k) => k != key)
                            })
                            setTeamInput((draft) => {
                                delete draft[key]
                            })
                        } else {
                            setDeleteTeam((draft) => {
                                return [...draft, key]
                            })
                        }
                    }}
                />
            </Table.Td>
        </Table.Tr>
    });

    return <Modal
            opened={props.opened}
            onClose={props.close}
            title={<Box style={{display:"flex", alignItems: "center", justifyContent:"center", width:"100%"}}>
                Teams Editor ⚙️
                <Space w="md" />
                <AddButton
                    onClick={()=>{
                        const newTeam = {
                            id: -1,
                            name: "",
                            short_name: "",
                            host: "",
                            created_at: new Date().toISOString()
                        }
                        const new_key = genNewKey()
                        setAddTeam((draft) => {
                            draft.push(new_key)
                        })
                        setTeamInput((draft) => {
                            draft[new_key] = newTeam
                        })
                    }}
                />
                <Space w="md" />
                <DoneButton
                    disabled={!isEdited}
                    onClick={()=>(async () => {
                        setError(null)
                        setLoading(true)
                        try{
                            if (Object.keys(deleteTeam).length > 0){
                                await deleteTeamList(Object.values(deleteTeam).map((k) => parseInt(k)))
                            }
                            if (Object.keys(deltaTeams).length > 0){
                                await editTeamList(Object.values(deltaTeams))
                            }
                            if (Object.keys(addTeam).length > 0){
                                await addTeamList(Object.values(deltaTeams))
                            }
                            notifications.show({title: "Teams Updated", message: "Teams have been updated successfully!", color: "green"})
                            reset()
                            status.refetch()
                        } catch (e){
                            setError((e as any).message)
                        } finally {
                            setLoading(false)
                        }
                    })()}
                />
            
            </Box>}
            size="xl"
            centered
            closeOnClickOutside={false}
    >
        {error==null?null:<Alert
            variant="light"
            color="red"
            title="Error in the configuration"
            icon={<MdError />}
        >
            {error}
        </Alert>}
        <Table stickyHeader stickyHeaderOffset={60}>
            <Table.Thead>
                <Table.Tr>
                    <Table.Th>ID</Table.Th>
                    <Table.Th>Name</Table.Th>
                    <Table.Th>Short Name</Table.Th>
                    <Table.Th>Host</Table.Th>
                    <Table.Th>Created at</Table.Th>
                    <Table.Th>Delete</Table.Th>
                </Table.Tr>
            </Table.Thead>
            <Table.Tbody>{rows}</Table.Tbody>
            <Table.Caption>{rows.length} teams</Table.Caption>
        </Table>
    </Modal>
}
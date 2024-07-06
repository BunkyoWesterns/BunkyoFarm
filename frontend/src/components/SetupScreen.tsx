import { setSetup, statusQuery } from "@/utils/queries";
import { AttackMode, SetupStatus } from "@/utils/types";
import { Alert, Badge, Box, Button, Container, Divider, NumberInput, PasswordInput, Space, Switch, TextInput } from "@mantine/core"
import { DateTimePicker } from '@mantine/dates';
import { useEffect, useMemo, useState } from "react";
import { useImmer } from "use-immer"
import { CancelActionButton, EditActionButton } from "./StatusIcon";
import { secondDurationToString } from "@/utils/time";
import { AttackModeControl } from "./Controllers";
import { WelcomeTitle } from "./WelcomeTitle";
import { useDebouncedCallback } from "@mantine/hooks";
import { notifications } from "@mantine/notifications";
import { MdError } from "react-icons/md";

export type ConfigDict = {
    FLAG_REGEX?: string,
    START_TIME?: Date|null,
    END_TIME?: Date|null,
    TICK_DURATION?: number,
    ATTACK_MODE?:AttackMode,
    LOOP_ATTACK_DELAY?: number,
    ATTACK_TIME_TICK_DELAY?: number,
    FLAG_TIMEOUT?: number|null,
    FLAG_SUBMIT_LIMIT?: number|null,
    SUBMIT_DELAY?: number,
    SUBMITTER?: number|null,
    SUBMITTER_TIMEOUT?: number,
    AUTHENTICATION_REQUIRED?: boolean,
    PASSWORD_HASH?: string|null,
    SETUP_STATUS?: SetupStatus,
    [key: string]: any
}

export const SetupScreen = () => {
    const [configInput, setConfigInput] = useImmer<ConfigDict>({})
    const status = statusQuery()
    useEffect(()=>{
        if (status.data?.config){
            setConfigInput(status.data.config as ConfigDict)
            if (status.data.config.PASSWORD_HASH !== null){
                setCustomPassword(false)
            }
        }
    }, [status.isLoading])
    const finalConfig = useMemo<ConfigDict>(()=>({ ...((status.data?.config??{}) as ConfigDict), ...configInput }), [configInput, status.isFetching])
    const deltaConfig = useMemo<ConfigDict>(()=>{
        let res:any = {}
        Object.keys(finalConfig).forEach((key)=>{
            if (((status.data?.config??{}) as ConfigDict)[key] !== finalConfig[key]){
                res[key] = finalConfig[key]
            }
        })
        return res
    }, [finalConfig, status.isFetching])
    const [customPassword, setCustomPassword] = useState(true)
    const [errorSetup, setErrorSetup] = useState<null|string>(null)

    return <Container>
        <Space h="xl" />
        <WelcomeTitle
            title="Exploitfarm Setup"
            description={<>This is the setup page. You can configure exploitfarm here.<br />This configuration is dinamically updated also during the execution.</>}
        />
        <Space h="xl" hiddenFrom="md" />
        <TextInput
            label={<>Regex [FLAG_REGEX]</>}
            placeholder="[A]{100,}="
            value={finalConfig.FLAG_REGEX}
            onChange={(e)=>setConfigInput((draft)=>{draft.FLAG_REGEX = e.currentTarget?.value??""})}
            withAsterisk
        />
        <Divider my="md" />
        <NumberInput
            label="Tick duration (in seconds) [TICK_DURATION]"
            placeholder="120"
            description={<>The tick interval is of <b><u>{secondDurationToString(finalConfig.TICK_DURATION??1)}</u></b></>}
            clampBehavior="strict"
            min={0}
            withAsterisk
            value={finalConfig.TICK_DURATION}
            onChange={(e)=>setConfigInput((draft)=>{draft.TICK_DURATION = parseInt(e.toString())})}
        />
        <Divider my="md" />

        <small>Attack strategies [ATTACK_MODE] <span style={{ color: "red" }}>*</span></small>
        <Space h="xs" />
        
        <Box style={{ width:"100%", flexWrap: "wrap", display:"flex" }}>
            <Box>
                <AttackModeControl 
                    onChange={
                        (v:AttackMode)=>setConfigInput((draft)=>{draft.ATTACK_MODE = v})
                    }
                    value={finalConfig.ATTACK_MODE??"tick-delay"}
                />
            </Box>
            <Box hiddenFrom="md" style={{ flexBasis: "100%", height:40 }} />
            <Space visibleFrom="md" w="lg" />
            <Box style={{ marginTop: -30, display: "flex", width:"100%", flex:1 }}>
                {
                    finalConfig.ATTACK_MODE == "tick-delay"?<>
                        <NumberInput
                            label="Tick time (in seconds) [TICK_DURATION]"
                            description={<>The attack delay is of <b><u>{secondDurationToString(finalConfig.TICK_DURATION??1)}</u></b></>}
                            value={finalConfig.TICK_DURATION}
                            style={{ width: "100%" }}
                            readOnly
                            disabled
                            min={0}
                        />
                    </>:
                    finalConfig.ATTACK_MODE == "loop-delay"?<>
                        <NumberInput
                            label="Attack delay (in seconds) [LOOP_ATTACK_DELAY]"
                            placeholder="120"
                            description={<>The attack delay is of <b><u>{secondDurationToString(finalConfig.LOOP_ATTACK_DELAY??1)}</u></b></>}
                            clampBehavior="strict"
                            min={0}
                            value={finalConfig.LOOP_ATTACK_DELAY}
                            onChange={(e)=>setConfigInput((draft)=>{draft.LOOP_ATTACK_DELAY = parseInt(e.toString())})}
                            style={{ width: "100%" }}
                        />
                    </>:
                    finalConfig.ATTACK_MODE == "wait-for-time-tick"?<>
                        <NumberInput
                            label="Start delay of the attack (in seconds) [ATTACK_TIME_TICK_DELAY]"
                            placeholder="120"
                            description={<>The attack will start at the start of the tick after <b><u>{secondDurationToString(finalConfig.ATTACK_TIME_TICK_DELAY??1)}</u></b></>}
                            clampBehavior="strict"
                            min={0}
                            value={finalConfig.ATTACK_TIME_TICK_DELAY}
                            onChange={(e)=>setConfigInput((draft)=>{draft.ATTACK_TIME_TICK_DELAY = parseInt(e.toString())})}
                            style={{ width: "100%" }}
                        />
                    </>:null
                }
            </Box>
        </Box>
        <Space hiddenFrom="md" h="sm" />
        <Divider my="md" />
        <Box className="center-flex" style={{ width: "100%" }}>
            <PasswordInput
                label="Password (in seconds) [PASSWORD_HASH]"
                description="Maximum time before the flag is marked as timeouted"
                placeholder="*******"
                disabled={!finalConfig.AUTHENTICATION_REQUIRED || (customPassword && status.data?.config?.PASSWORD_HASH !== null)}
                style={{ width: "100%", marginRight: 10, opacity: finalConfig.AUTHENTICATION_REQUIRED?1:0.5}}
                value={finalConfig.PASSWORD_HASH??""}
                onChange={(e)=>setConfigInput((draft)=>{draft.PASSWORD_HASH = e.currentTarget?.value??""})}
            />
            {(status.data?.config?.PASSWORD_HASH !== null && finalConfig.AUTHENTICATION_REQUIRED)?
                <>{!customPassword?<Box>
                        <EditActionButton
                            onClick={()=>{
                                setCustomPassword(true)
                                setConfigInput((draft)=>{draft.PASSWORD_HASH = ""})
                            }}
                            style={{ marginTop: 43 }}
                            disabled={!finalConfig.AUTHENTICATION_REQUIRED}
                        />
                    </Box>:<Box>
                        <CancelActionButton
                            onClick={()=>{
                                setCustomPassword(false)
                                setConfigInput((draft)=>{draft.PASSWORD_HASH = undefined})
                            }}
                            style={{ marginTop: 43 }}
                        />
                        
                    </Box>
                }<Space w="md" /></>
            :null}
            
            <Switch
                checked={finalConfig.AUTHENTICATION_REQUIRED}
                onChange={() => setConfigInput((draft)=>{
                    if (finalConfig.AUTHENTICATION_REQUIRED){
                        draft.PASSWORD_HASH = null
                        draft.AUTHENTICATION_REQUIRED = false
                        setCustomPassword(false)
                    }else{
                        draft.PASSWORD_HASH = ""
                        draft.AUTHENTICATION_REQUIRED = true
                        setCustomPassword(true)
                    }
                })}
                color="teal"
                size="md"
                style={{ marginTop: 43 }}
            />
        </Box>
        <Divider my="md" />
        <NumberInput
            withAsterisk
            label="Sumbitter max timeout for execution (in seconds) [SUBMITTER_TIMEOUT]"
            description="Maximum time for the submitter to execute"
            placeholder="30"
            clampBehavior="strict"
            min={1}
            disabled={finalConfig.SUBMITTER_TIMEOUT === null}
            style={{ width: "100%", marginRight: 10, opacity: (finalConfig.SUBMITTER_TIMEOUT !== null)?1:0.5}}
            value={finalConfig.SUBMITTER_TIMEOUT??0}
            onChange={(e)=>setConfigInput((draft)=>{draft.SUBMITTER_TIMEOUT = parseInt(e.toString())})}
        />
        <Space h="md" />
        <Box className="center-flex" style={{ width: "100%" }}>
            <NumberInput
                label="Max flags per submit [FLAG_SUBMIT_LIMIT]"
                description="Maximum number of flag submittable per submit execution"
                placeholder="500"
                clampBehavior="strict"
                min={0}
                disabled={finalConfig.FLAG_SUBMIT_LIMIT === null}
                style={{ width: "100%", marginRight: 10, opacity: (finalConfig.FLAG_SUBMIT_LIMIT !== null)?1:0.5}}
                value={finalConfig.FLAG_SUBMIT_LIMIT??100}
                onChange={(e)=>setConfigInput((draft)=>{draft.FLAG_SUBMIT_LIMIT = parseInt(e.toString())})}
            />
            <Switch
                checked={finalConfig.FLAG_SUBMIT_LIMIT !== null}
                onChange={() => setConfigInput((draft)=>{draft.FLAG_SUBMIT_LIMIT = finalConfig.FLAG_SUBMIT_LIMIT !== null?null:500})}
                color="teal"
                size="md"
                style={{ marginTop: 43 }}
            />
        </Box>
        <Divider my="md" />
        <Box className="center-flex" style={{ width: "100%" }}>
            <NumberInput
                label="Flag timeout (in seconds) [FLAG_TIMEOUT]"
                description="Maximum time before the flag is marked as timeouted"
                placeholder="100"
                clampBehavior="strict"
                min={0}
                disabled={finalConfig.FLAG_TIMEOUT === null}
                style={{ width: "100%", marginRight: 10, opacity: (finalConfig.FLAG_TIMEOUT !== null)?1:0.5}}
                value={finalConfig.FLAG_TIMEOUT??0}
                onChange={(e)=>setConfigInput((draft)=>{draft.FLAG_TIMEOUT = parseInt(e.toString())})}
            />
            <Switch
                checked={finalConfig.FLAG_TIMEOUT !== null}
                onChange={() => setConfigInput((draft)=>{draft.FLAG_TIMEOUT = finalConfig.FLAG_TIMEOUT !== null?null:draft.TICK_DURATION??1})}
                color="teal"
                size="md"
                style={{ marginTop: 43 }}
            />
        </Box>
        <Divider my="md" />
        <Box className="center-flex" style={{ width: "100%" }}>
            <DateTimePicker
                withSeconds
                label="Start time [START_TIME]"
                value={finalConfig.START_TIME}
                placeholder="Starting time of the competition"
                description={<>Timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}</>}
                onChange={(e)=>setConfigInput((draft)=>{draft.START_TIME = e})}
                style={{ width: "100%", marginRight: 10}}
            />
            <CancelActionButton
                disabled={finalConfig.START_TIME === null}
                onClick={()=>{
                    setConfigInput((draft)=>{draft.START_TIME = null})
                }}
                style={{ marginTop: 43 }}
            />
        </Box>
        <Space h="md" />
        <Box className="center-flex" style={{ width: "100%" }}>
            <DateTimePicker
                withSeconds
                label="End time [END_TIME]"
                placeholder="Ending time of the competition"
                value={finalConfig.END_TIME}
                description={<>Timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}</>}
                onChange={(e)=>setConfigInput((draft)=>{draft.END_TIME = e})}
                style={{ width: "100%", marginRight: 10}}
            />
            <CancelActionButton
                disabled={finalConfig.END_TIME === null}
                onClick={()=>{
                    setConfigInput((draft)=>{draft.END_TIME = null})
                }}
                style={{ marginTop: 43 }}
            />
        </Box>
        <Divider my="md" />
        <Box className="center-flex" style={{justifyContent:"left"}}>
            <Box style={{ flexGrow:1 }} hiddenFrom="md" />
            <Badge
                size="lg"
                variant="gradient"
                gradient={{ from: 'red', to: 'grape', deg: 156 }}
                >
                <u>Submitter</u> {<>{status.data?.submitter?.name??"Not set!"}</>}
            </Badge>
            <Space w="md" />
            <Badge
                size="lg"
                variant="gradient"
                gradient={{ from: 'blue', to: 'teal', deg: 156 }}
                >
                <u>Teams</u> {<>{status.data?.teams?.length??0}</>}
            </Badge>
            <Box style={{ flexGrow:1 }} hiddenFrom="md" />
        </Box>
        <Space h="xl" />
        {errorSetup==null?null:<Alert
            variant="light"
            color="red"
            title="Error in the configuration"
            icon={<MdError />}
        >
            {errorSetup}
        </Alert>}
        <Space h="xl" />
        <Box className="center-flex" style={{ flexWrap: "wrap" }}>
            <Button
                color="red"
                size="md"
                onClick={()=>{
                    notifications.show({
                        message: "Implement me please :("
                    })
                }}
            >
                Teams 🚀
            </Button>
            <Space w="xl" />
            <Button
                color="lime"
                size="md"
                onClick={()=>{
                    notifications.show({
                        message: "Implement me please :("
                    })
                }}
            >
                Submitter 🚩
            </Button>
            <Box visibleFrom="md" style={{flexGrow: 1}} />
            <Box hiddenFrom="md" style={{ flexBasis: "100%", height:40 }} />
            <Button
                color="blue"
                size="lg"
                onClick={()=>{
                    setSetup({...deltaConfig, SETUP_STATUS: "running"} as ConfigDict).then(()=>{
                        setErrorSetup(null)
                        status.refetch()
                    }).catch((e)=>{
                        setErrorSetup(e.message as string)
                    })
                }}
            >
                Start Exploiting 👾 🚩
            </Button>
        </Box>
        <Space h="xl" />
        <Space h="xl" />
        <Space h="xl" />
    </Container>
}

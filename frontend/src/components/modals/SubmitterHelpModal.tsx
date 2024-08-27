import { Accordion, Modal, Space, Title } from "@mantine/core"
import { IoLibrary } from "react-icons/io5";
import { FaSearchPlus } from "react-icons/fa";
import { BsPatchQuestionFill } from "react-icons/bs";
import { FaList } from "react-icons/fa";
import { BsPersonWorkspace } from "react-icons/bs";
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';

import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import { srcery } from 'react-syntax-highlighter/dist/esm/styles/hljs';
SyntaxHighlighter.registerLanguage('python', python);

export const SubmitterHelpModal = ({ open, onClose }:{ open:boolean, onClose:()=>void}) => {

    return <Modal opened={open} onClose={onClose} title="Submitter help guide 💬" size="xl" centered>
        <Title order={3}>How can I build my submitter code?</Title>
        <p>Before your code is interted into the system, it is checked about some requirements to allow the compatibility with the system itself.</p>  
        <Title order={3}>Basic submitter requirements and rules</Title>
        <p>The submitter must be written in <u>python</u> (exploits instead can be written in the language you want to use)</p>
        <p>The system will execute the <u><b><code>submit</code></b></u> function every time a new submission is made. This function must have the following signature:</p>
        <SyntaxHighlighter language="python" showLineNumbers style={srcery}>
{`from exploitfarm import FlagStatus
import requests, pwntools

def submit(flags):
    # flag submission code
    return [
        ("FLAG{}", FlagStatus.ok, "The flag is correct!")
        # FLAG       STATUS     ADDITIONAL MESSAGE WITH INFO
    ]`}
        </SyntaxHighlighter>
        <p>
            The submit function must be defined in the global context, and the first paramether required <u>must be called flags</u>. 
            Here you will recieve a list of flags to submit (you can limit the max size of this list in the setup page, event at 1 flag at time).
        </p>

        <p>
            The script will be killed after a timeout (setted on the setup page),
            <b>Setting always a max limit of flags that can be submitted at time usually is a good practice</b> to avoid submitting too many data in a single time,
            and avoiding the possibility to timeout the submitter making it unable to submit flags anymore!
        </p>
        <p>All the paramethers and also the submitter code can be changed also during the execution of exploitfarm.</p>
        <p>The submitter function must return a list of tuple containing: the flag, the status of the submission (more details on Q/A for statuses) and an addictional message.</p>
        <p>This is necessary to make the submitter working correctly, <b>return data is not checked at submitter creation but if not done correctly could create problems</b></p>
        <Title order={3}>Advanced submitter (parametrized submitter)</Title>
        <p>The aim of exploitfarm is to build general submitters and allow to change only some paramether to make them work in the next A/D.</p>
        <p>For this reason (and also to make automatic scripts more easy to build and customize) submit function can accept additional paramethers totally customizable without changing the code itself:</p>
        <SyntaxHighlighter language="python" showLineNumbers style={srcery}>
{`from exploitfarm import FlagStatus
import requests

def submit(flags, http_url: str = 'http://game-server/submit', token):
    # flag submission code
    return requests.post(http_url, data={ "flags": flags, "token": token }).json()`}
        </SyntaxHighlighter>

        <p>How are managed the additional paramether of submit function?</p>
        <p>Additional paramethers are analyzed by exploitfarm and can parametrized: under the code editor you will see that additional paramether will be showen and you will be able to customize the value set for that specific argument</p>
        <p>
            You can set a specific type of the paramether using annotation, and if done the type will be enforced (e.g. if you set 'str' exploitfarm will reject an int argument).
            This is done only for the following types: <b>[int, str, bool, float]</b>. If the type is not set or is set a type that is not included in the previous list, the type will not be enforced
        </p>
        <p>
            If you set a default value and don't specify a paramether for that, the default value will be used.
            At the same time, if you set another value for that paramether, the default value will be overwritten.
        </p>

        <Space h="md" /><Title order={3}>Q/A about the submitter</Title><Space h="md" />

        <Accordion variant="contained">
            <Accordion.Item value="what-flag-status-exists">
                <Accordion.Control icon={<BsPatchQuestionFill />}>What is 'FlagStatus' class and how statuses works?</Accordion.Control>
                <Accordion.Panel>
                    <p>The FlagStatus class imported by exploitfarm lib can be one of the following:</p>
                    <SyntaxHighlighter language="python" showLineNumbers style={srcery}>
{`class FlagStatus:
    wait = 'wait'
    timeout = 'timeout'
    invalid = 'invalid'
    ok = 'ok'`}
                    </SyntaxHighlighter>
                    <Space h="md" />
                    <Title order={3}>Wait status</Title>
                    <p>Use wait if there was some problem with the submission and you want to try again in the next cycle</p>
                    <Title order={3}>Timeout status</Title>
                    <p>Use timeout if the submission was not valid (the flag has expired) and you don't want to try again.
                    Note: Timeout status is automatically set if the flag is expired according to the configuration you set in the setup page</p>
                    <Title order={3}>Invalid status</Title>
                    <p>Use invalid if the flag was not valid, so rejected by the system</p>
                    <Title order={3}>Ok status</Title>
                    <p>Use ok if the flag was valid and accepted by the system</p>
                </Accordion.Panel>
            </Accordion.Item>
            <Accordion.Item value="what-libraries-can-i-use">
                <Accordion.Control icon={<IoLibrary />}>What python libraries I can use in my code?</Accordion.Control>
                <Accordion.Panel>
                    <p>By default are installed the following libraries (that are enough for most cases)</p>
                    <p><b>["requests", "pwnools", "exploitfarm"]</b></p>
                </Accordion.Panel>
            </Accordion.Item>
            <Accordion.Item value="i-need-extra-libraries">
                <Accordion.Control icon={<FaSearchPlus />}>And what if I need extra requirements?</Accordion.Control>
                <Accordion.Panel>
                    <p>If you need to use other libraries your need to rebuild the exploitfarm container (if you don't delete the volume associated, the data won't be lost):</p>
                    <ol>
                        <li>Stop this execution of exploitfarm</li>
                        <li>If not already done, now you need to clone the entire repository</li>
                        <li>Go to backend/requirements.txt and add the library you want to use</li>
                        <li>Build and start the container with <code>python3 start.py -b</code> (-b will build the container from sourcecode and not from github, all clients will give a warning about the version that when built from source will be 0.0.0, don't worry you can skipp the warning)</li>
                        <li>Now the extra libraries are installed and you can use them in your new exploitfarm!</li>
                    </ol>
                </Accordion.Panel>
            </Accordion.Item>
            <Accordion.Item value="can-i-return-an-iterator">
                <Accordion.Control icon={<FaList />}>Can I return an iterator instead of a list? (e.g. usign yield)</Accordion.Control>
                <Accordion.Panel>
                    <p>Yes you can use yield, before the submitter read the result arrived by the submitter cast it with list() to allow also the use of iterators</p>
                </Accordion.Panel>
            </Accordion.Item>
            <Accordion.Item value="can-you-provide-me-an-example">
                <Accordion.Control icon={<BsPersonWorkspace />}>Let me see an example</Accordion.Control>
                <Accordion.Panel>
                    <p>Heres the submitter built for <a href="https://cyberchallenge.it" target="_blank" >CyberChallenge 2024</a>:</p>
                    <SyntaxHighlighter language="python" showLineNumbers style={srcery}>
{`import requests
from exploitfarm import FlagStatus

RESPONSES = {
    FlagStatus.timeout: ['timeout'],
    FlagStatus.ok: ['accepted', 'congrat'],
    FlagStatus.invalid: ['bad', 'wrong', 'expired', 'unknown', 'your own',
        'too old', 'not in database', 'already', 'invalid', 'nop team', 'game over', 'no such flag'],
    FlagStatus.wait: [
        'try again later', 'is not up', 'game not started'
    ]
}

def submit(flags, token:str = None, http_timeout:int=30, url:str="http://10.10.0.1:8080/flags"):
    r = requests.put(url, headers={ 'X-Team-Token': token }, json=flags, timeout=http_timeout)
    if r.status_code == 429:
        for flag in flags:
            yield (flag, FlagStatus.wait, "Too many requests. Error 429")
    else:
        req_response = r.json()
        if not isinstance(req_response, list):
            raise ValueError(f"Unexpected response. {req_response}")
        for i, item in enumerate(req_response):
            
            if not isinstance(item, dict):       
                yield (flags[i], FlagStatus.wait, "Unexpected response. Error 429")
            
            response = item['msg']
            response = response.split("]")
            if len(response) > 1: response = response[1]
            else: response = response[0]
            
            response_lower = response.strip().lower()
            for status, substrings in RESPONSES.items():
                if any(s in response_lower for s in substrings):
                    found_status = status
                    break
            else:
                found_status = FlagStatus.wait

            yield (item['flag'], found_status, response)`}
                    </SyntaxHighlighter>
                </Accordion.Panel>
            </Accordion.Item>
        </Accordion>
    </Modal>
}
## Chat History
### human
To speed up the audio processing in your application, you should divide the audio into chunks and upload each chunk while the next one is being recorded. This involves tracking the duration of the current audio chunk, creating a new chunk when the duration reaches a certain length, and starting the recording of the next chunk immediately. You'll also need to manage multiple chunks and modify your stop function to stop the recording of the current chunk, upload it, and then stop the overall recording process.


Remember, these changes involve asynchronous operations and careful timing, so they can be quite complex. It's important to design and test each step carefully.To implement the chunking and parallel uploading, you'll need to modify your existing functions and potentially add new ones. Here's a high-level overview of the changes:

1. **Tracking Duration**: You'll need to track the duration of the current audio chunk. This can be done by adding a timestamp when the recording starts and then checking the elapsed time in your `onaudioprocess` function. Once the duration of a chunk reaches your desired length (e.g., 5 seconds), you can trigger the next steps.

2. **Creating Audio Chunks**: You'll need to modify your `onaudioprocess` function to create audio chunks. Currently, it appends all audio data to `leftchannel` and `rightchannel`. Instead, you should create a new chunk (i.e., a new pair of channels) every time the duration reaches your chunk length. 

3. **Uploading Chunks**: When a chunk is ready, you should call a new function, say `uploadChunk`, which will handle the encoding and uploading of that chunk. This function will be similar to your existing `stop` function, but it will work on a single chunk instead of the entire recording. 

4. **Starting New Chunks**: After a chunk is sent for uploading, you should start recording the next chunk immediately. This means starting a new pair of channels and a new timestamp.

5. **Managing Chunks**: You'll need to manage multiple chunks, each with its own channels, timestamp, and potentially its own `MediaStream` and `ScriptProcessorNode`. This could be done by creating a new class or interface representing a chunk, or by using data structures like arrays or maps.

6. **Stopping the Recording**: Your `stop` function will need to be modified to stop the recording of the current chunk, upload it, and then stop the overall recording process.

Remember, these changes involve asynchronous operations and careful timing, so they can be quite complex. It's important to design and test each step carefully.

Here is the original code:

```typescript
import { library } from '@fortawesome/fontawesome-svg-core';
import { fas } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { ReactNode } from "react";
import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection
} from "streamlit-component-lib";
import { AssemblyAI } from 'assemblyai';


library.add(fas)

// BAD IDEA BAD IDEA BAD IDEA, FIX LATER
const apiKey = process.env.REACT_APP_ASSEMBLYAI_API_KEY as string;

const client = new AssemblyAI({
  apiKey: apiKey,
});

interface AudioRecorderState {
  color: string
  status: string
}

interface AudioData {
  blob: Blob
  url: string
  type: string
}

interface AudioRecorderProps {
  args: Map<string, any>
  width: number
  disabled: boolean
}

async function uploadAudio(data: AudioData): Promise<string> {
  // Function to upload audio to AssemblyAI, returns the url for the audio 
  let audioUrl = '';

  try {
    // Prepare the request options including the API key for AssemblyAI
    const requestOptions = {
      method: 'POST',
      headers: {
        'Authorization': apiKey,
        'Content-Type': 'application/octet-stream',
      },
      body: data.blob,
    };

    // Perform the upload to AssemblyAI
    const uploadResponse = await fetch('https://api.assemblyai.com/v2/upload', requestOptions);
    const uploadResult = await uploadResponse.json();

    if (uploadResponse.ok) {
      audioUrl = uploadResult.upload_url;
      return audioUrl;
    }
    else {
      throw new Error('Audio upload failed: ' + uploadResult.error);
    }
  } catch (error) {
    console.error(error);
    return 'An error occurred while uploading the audio: ';
  }
}

class AudioRecorder extends StreamlitComponentBase<AudioRecorderState> {
  public constructor(props: AudioRecorderProps) {
    super(props)
    this.state = { color: this.props.args["neutral_color"], status: ""}
  }

  stream: MediaStream | null = null;
  // AudioContext = window.AudioContext || window.webkitAudioContext;
  AudioContext = (window as any).AudioContext || (window as any).webkitAudioContext;

  type: string = "audio/wav";
  sampleRate: number | null = null;
  phrase_buffer_count: number | null = null;
  pause_buffer_count: number | null = null;
  pause_count: number = 0;
  stage: string | null = null;
  volume: any = null;
  audioInput: any = null;
  analyser: any = null;
  recorder: any = null;
  recording: boolean = false;
  leftchannel: Float32Array[] = [];
  rightchannel: Float32Array[] = [];
  leftBuffer: Float32Array | null = null;
  rightBuffer: Float32Array | null = null;
  recordingLength: number = 0;
  tested: boolean = false;

  // Click debounce
  private lastClick = Date.now();

  //get mic stream
  getStream = (): Promise<MediaStream> => {
    return navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  };

  setupMic = async () => {
    try {
      // window.stream = this.stream = await this.getStream();
      (window as any).stream = this.stream = await this.getStream();
    } catch (err) {
      console.log("Error: Issue getting mic", err);
    }

    this.startRecording();
  };

  closeMic = () => {
    this.stream!.getAudioTracks().forEach((track) => {
      track.stop();
    });
    this.audioInput.disconnect(0);
    this.analyser.disconnect(0);
    this.recorder.disconnect(0);
  };

  writeUTFBytes = (view: DataView, offset: number, string: string) => {
    let lng = string.length;
    for (let i = 0; i < lng; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  mergeBuffers = (channelBuffer: Float32Array[], recordingLength: number) => {
    let result = new Float32Array(recordingLength);
    let offset = 0;
    let lng = channelBuffer.length;
    for (let i = 0; i < lng; i++) {
      let buffer = channelBuffer[i];
      result.set(buffer, offset);
      offset += buffer.length;
    }
    return result;
  };

  interleave = (leftChannel: Float32Array, rightChannel: Float32Array) => {
    let length = leftChannel.length + rightChannel.length;
    let result = new Float32Array(length);

    let inputIndex = 0;

    for (let index = 0; index < length; ) {
      result[index++] = leftChannel[inputIndex];
      result[index++] = rightChannel[inputIndex];
      inputIndex++;
    }
    return result;
  };

  startRecording = () => {
    let input_sample_rate = this.props.args["sample_rate"];
    if (input_sample_rate === null) {
      this.context = new this.AudioContext();
      this.sampleRate = this.context.sampleRate;
    } else {
      this.context = new this.AudioContext(
        {"sampleRate": input_sample_rate}
      );
      this.sampleRate = input_sample_rate;
    }
    console.log(`Sample rate ${this.sampleRate}Hz`);
  
    // create buffer states counts
    let bufferSize = 2048;
  
    // creates a gain node
    this.volume = this.context.createGain();
  
    // creates an audio node from the microphone incoming stream
    this.audioInput = this.context.createMediaStreamSource(this.stream);
  
    // Create analyser
    this.analyser = this.context.createAnalyser();
  
    // connect audio input to the analyser
    this.audioInput.connect(this.analyser);
  
    this.recorder = this.context.createScriptProcessor(bufferSize, 2, 2);
  
    this.analyser.connect(this.recorder);
  
    // finally connect the processor to the output
    this.recorder.connect(this.context.destination);
  
    const self = this;  // to reference component from inside the function
    this.recorder.onaudioprocess = function (e: any) {
      // Check
      if (!self.recording) return;
      // Do something with the data, i.e Convert this to WAV
      let left = e.inputBuffer.getChannelData(0);
      let right = e.inputBuffer.getChannelData(1);
  
      // we clone the samples
      self.leftchannel.push(new Float32Array(left));
      self.rightchannel.push(new Float32Array(right));
      self.recordingLength += bufferSize;
    };
  };

  start = async () => {
    this.recording = true;
    this.setState({
      color: this.props.args["recording_color"],
      status: "recording..."
    })
    await this.setupMic();
    // reset the buffers for the new recording
    this.leftchannel.length = this.rightchannel.length = 0;
    this.recordingLength = 0;    
  };

  stop = async () => {
    this.recording = false;
    this.setState({
      color: this.props.args["neutral_color"]
    })
    this.closeMic();
    console.log(this.recordingLength);

    // we flat the left and right channels down
    this.leftBuffer = this.mergeBuffers(this.leftchannel, this.recordingLength);
    this.rightBuffer = this.mergeBuffers(
      this.rightchannel,
      this.recordingLength
    );
    // we interleave both channels together
    let interleaved = this.interleave(this.leftBuffer, this.rightBuffer);

    ///////////// WAV Encode /////////////////
    // from http://typedarray.org/from-microphone-to-wav-with-getusermedia-and-web-audio/
    //

    // we create our wav file
    let buffer = new ArrayBuffer(44 + interleaved.length * 2);
    let view = new DataView(buffer);

    // RIFF chunk descriptor
    this.writeUTFBytes(view, 0, "RIFF");
    view.setUint32(4, 44 + interleaved.length * 2, true);
    this.writeUTFBytes(view, 8, "WAVE");
    // FMT sub-chunk
    this.writeUTFBytes(view, 12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    // stereo (2 channels)
    view.setUint16(22, 2, true);
    view.setUint32(24, this.sampleRate!, true);
    view.setUint32(28, this.sampleRate! * 4, true);
    view.setUint16(32, 4, true);
    view.setUint16(34, 16, true);
    // data sub-chunk
    this.writeUTFBytes(view, 36, "data");
    view.setUint32(40, interleaved.length * 2, true);

    // write the PCM samples
    let lng = interleaved.length;
    let index = 44;
    let volume = 1;
    for (let i = 0; i < lng; i++) {
      view.setInt16(index, interleaved[i] * (0x7fff * volume), true);
      index += 2;
    }

    // our final binary blob
    const blob = new Blob([view], { type: this.type });
    const audioUrl = URL.createObjectURL(blob);


    await this.onStop({
      blob: blob,
      url: audioUrl,
      type: this.type,
    });

  };

  
  private onClicked = async () => {
    // Debounce time in milliseconds
    const debounceTime = 1000;
    
    // Current time
    const now = Date.now();
    
    // If time since last click is less than debounceTime, ignore the click
    if (now - this.lastClick < debounceTime) {
      return;
    }
    
    // Update last click time
    this.lastClick = now;
  
    console.log("Clicked")
    if (!this.recording){
      await this.start()
    } else {
      await this.stop()
    }
  }
  
  private onStop = async (data: AudioData) => {
    // make microphone yellow
    this.setState({
      color: "#FFD700",
      status: "transcribing..."
    })
    var audioUrl = await uploadAudio(data);
    console.log(audioUrl);
    Streamlit.setComponentValue(audioUrl);
    this.setState({
      color: this.props.args["neutral_color"],
      status: ""
    })
  };

  public render = (): ReactNode => {
    const { theme } = this.props
    if (theme) {
      // Maintain compatibility with older versions of Streamlit that don't send
      // a theme object.
    }

    return (
      <span>
        <FontAwesomeIcon
        // @ts-ignore
        icon={this.props.args["icon_name"]}
        onClick={this.onClicked}
        style={{color:this.state.color}}
        size={this.props.args["icon_size"]}
        />
        <br/>
        &nbsp; {this.state.status}
      </span>
    )
  }
}

export default withStreamlitConnection(AudioRecorder)
```

Start by writting the code for the functions needed to do steps 1, 2, and 3. You are starting by tracking the duration of the audio stream, and queuing the audio chunks for upload. Everything else can wait till later.


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

interface TranscriptChunk {
  id: number;
  transcript: string | null;
}

interface AudioRecorderProps {
  args: Map<string, any>
  width: number
  disabled: boolean
}

async function uploadAudio(data: AudioData): Promise<string | null> {
  let audioUrl = null;
  const maxRetries = 2;
  let attempt = 0;

  while (attempt < maxRetries) {
    try {
      const requestOptions = {
        method: 'POST',
        headers: {
          'Authorization': apiKey,
          'Content-Type': 'application/octet-stream',
        },
        body: data.blob,
      };

      const uploadResponse = await fetch('https://api.assemblyai.com/v2/upload', requestOptions);
      const uploadResult = await uploadResponse.json();

      if (uploadResponse.ok) {
        audioUrl = uploadResult.upload_url;
        return audioUrl;
      } else {
        throw new Error('Audio upload failed: ' + uploadResult.error);
      }
    } catch (error) {
      console.error(`Attempt ${attempt + 1} failed:`, error);
      if (attempt === maxRetries - 1) {
        return null; // Return null after all attempts fail
      }
    }
    attempt++;
  }

  return audioUrl;
}

async function transcribeAudio(url: string): Promise<string | null> {
  let transcriptText = null;
  const maxRetries = 2;
  let attempt = 0;

  while (attempt < maxRetries) {
    try {
      let transcript = await client.transcripts.transcribe({
        audio: url,
      });

      if (transcript.status === 'completed') {
        transcriptText = transcript.text as string;
        return transcriptText;
      } else {
        throw new Error('Transcription failed: ' + transcript.status);
      }
    } catch (error) {
      console.error(`Attempt ${attempt + 1} failed:`, error);
      if (attempt === maxRetries - 1) {
        return null; // Return null after all attempts fail
      }
    }
    attempt++;
  }

  return transcriptText;
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

  // Custom properties
  status_msg: string = ""; // Status message to be displayed 

  // Properties for audio chunking
  transcript: string = ""; // Holds the ongoing transcript
  chunkLength: number = 12000; // Length of each chunk in milliseconds
  currentChunkStartTime: number | null = null; // Start time of the current chunk
  chunksInProcessing: number = 0; // Number of chunks currently being processed
  chunkArray: TranscriptChunk[] = [];
  nextChunkId: number = 0;

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
      // Check if the current chunk has reached the desired length
      if (Date.now() - self.currentChunkStartTime! >= self.chunkLength) {
        // Process the current chunk without stopping the recording
        self.handleChunk();
        // Reset the buffers for the new chunk
        self.leftchannel.length = self.rightchannel.length = 0;
        self.recordingLength = 0;
        // Start timer of the next chunk
        self.currentChunkStartTime = Date.now();
      }
    };
  
    // Initialize the current chunk start time
    this.currentChunkStartTime = Date.now();
  };

  start = async () => {
    this.recording = true;
    this.transcript = ""; // Reset the transcript at the start of a new recording
    this.status_msg = "[Recording...]";
    this.setState({
      color: this.props.args["recording_color"],
      status: this.status_msg
    })
    await this.setupMic();
    // reset the buffers for the new recording
    this.leftchannel.length = this.rightchannel.length = 0;
    this.recordingLength = 0;    
  };

  stop = async () => {
    this.recording = false;

    this.status_msg = "[Processing...]";
    this.setState({
      color: '#FFD700',
      status: this.status_msg + " " + this.transcript
    });
    
    // Call handleChunk for the last chunk processing
    this.handleChunk();
  
    // Wait for the chunkProcessingComplete flag to be set to true
    await new Promise<void>(resolve => {
      const checkProcessing = () => {
        if (this.chunksInProcessing === 0) {
          resolve();
        } else {
          // Check the flag every 100 milliseconds
          setTimeout(checkProcessing, 100);
        }
      };
      checkProcessing();
    });
  
    // Proceed to stop the microphone and update the UI
    this.closeMic();

    this.status_msg = "[Recording Complete]";
    this.setState({
      color: '#00FF00', // Green
      status: this.status_msg + " " + this.transcript
    });

    Streamlit.setComponentValue(this.transcript);
  };

  private createChunk = (): AudioData => {
    // We flat the left and right channels down
    this.leftBuffer = this.mergeBuffers(this.leftchannel, this.recordingLength);
    this.rightBuffer = this.mergeBuffers(
      this.rightchannel,
      this.recordingLength
    );
    // we interleave both channels together
    let interleaved = this.interleave(this.leftBuffer, this.rightBuffer);

    ///////////// WAV Encode /////////////////
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

    // Create an audioData object for the chunk
    const chunk: AudioData = {
      blob: blob,
      url: URL.createObjectURL(blob),
      type: this.type
    };

    return chunk;
  };
  
  private onClicked = async () => {
    //// CLICK DEBOUNCE ////
    const debounceTime = 1000;
    // Current time
    const now = Date.now();
    // If time since last click is less than debounceTime, ignore the click
    if (now - this.lastClick < debounceTime) {
      return;
    }

    //// BUTTON LOGIC ////
    this.lastClick = now;
    if (!this.recording){
      await this.start()
    } else {
      await this.stop()
    }
  }

  private handleChunk = async () => {
    this.chunksInProcessing++;
    const chunk = this.createChunk();
    let chunkUrl = await uploadAudio(chunk);
    if (chunkUrl === null) {
      this.setState({
        status: "Chunk upload failed"
      })
      return;
    }
    let chunkTranscription = await transcribeAudio(chunkUrl);
    // Assign an ID to the chunk and add it to the chunks array
    this.chunkArray.push({ id: this.nextChunkId++, transcript: chunkTranscription });
    this.updateTranscript(); // Call the new method to update the transcript
    this.chunksInProcessing--;
  };

  private updateTranscript = () => {
    // Sort chunks by their ID to ensure correct order
    this.chunkArray.sort((a, b) => a.id - b.id);
    // Build the transcript from the sorted chunks
    this.transcript = this.chunkArray.map(chunk => chunk.transcript).join(" ");
    // Update the component state to reflect the new transcript
    this.setState({
      status: this.status_msg + " " + this.transcript
    });
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
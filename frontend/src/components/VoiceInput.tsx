import React, { useState, useRef } from 'react';
import { Button, Tooltip, message } from 'antd';
import { AudioOutlined, LoadingOutlined } from '@ant-design/icons';
import { getBaseUrl } from '@/utils/base_api';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export const VoiceInput: React.FC<VoiceInputProps> = ({ onTranscript, disabled = false }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // 开始录音
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        await processAudio(audioBlob);
        
        // 停止所有音轨
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('无法访问麦克风:', error);
      message.error('无法访问麦克风，请检查权限设置');
    }
  };

  // 停止录音
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // 处理音频 - 使用硅基流动 SenseVoiceSmall API
  const processAudio = async (audioBlob: Blob) => {
    setIsProcessing(true);
    try {
      // 使用硅基流动的 SenseVoiceSmall 模型
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('model', 'sensevoice'); // 使用硅基流动的模型
      formData.append('language', 'zh'); // 指定中文

      // 调用后端语音识别 API
      // 需要包含认证信息
      const token = localStorage.getItem('access_token');
      const headers: any = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const baseUrl = getBaseUrl() || window.location.origin;
      const response = await fetch(`${baseUrl}/api/speech-to-text`, {
        method: 'POST',
        headers: headers,
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        console.log('语音识别响应:', data); // 调试日志
        
        // 后端返回的是 success_response 格式，文本在 data.data.text 中
        if (data.status === 'ok' && data.data && data.data.text) {
          const transcript = data.data.text.trim();
          if (transcript) {
            onTranscript(transcript);
            message.success('语音识别成功');
          } else {
            message.warning('未识别到有效内容，请重试');
          }
        } else if (data.text) {
          // 兼容直接返回 text 的情况
          onTranscript(data.text);
        } else {
          throw new Error('响应格式错误');
        }
      } else {
        const errorData = await response.json();
        console.error('语音识别失败:', errorData);
        throw new Error(errorData.msg || '转换失败');
      }
    } catch (error) {
      console.error('语音转文字失败:', error);
      
      // 方案2：降级到浏览器内置的 Web Speech API (仅支持 Chrome)
      if ('webkitSpeechRecognition' in window) {
        const recognition = new (window as any).webkitSpeechRecognition();
        recognition.lang = 'zh-CN';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          onTranscript(transcript);
        };

        recognition.onerror = (event: any) => {
          console.error('语音识别错误:', event);
          message.error('语音识别失败，请重试');
        };

        // 将音频转换为可播放的 URL
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        recognition.start();
        // 注意：Web Speech API 需要实时音频流，这里只是示例
      } else {
        message.error('语音转文字服务暂时不可用');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <Tooltip title={isRecording ? "点击停止录音" : "点击开始录音"}>
      <Button
        type="text"
        icon={isProcessing ? <LoadingOutlined /> : <AudioOutlined />}
        onClick={handleClick}
        disabled={disabled || isProcessing}
        style={{
          color: isRecording ? '#ff4d4f' : undefined,
          animation: isRecording ? 'pulse 1.5s infinite' : undefined,
        }}
      />
      <style jsx>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      `}</style>
    </Tooltip>
  );
};

export default VoiceInput;
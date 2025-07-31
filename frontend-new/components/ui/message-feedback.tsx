"use client";

import React, { useState } from "react";
import { ThumbsUp, ThumbsDown, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { 
  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface MessageFeedbackProps {
  messageId: string;
  onFeedback?: (messageId: string, rating: 'thumbs_up' | 'thumbs_down', comment?: string) => Promise<void>;
  className?: string;
}

export function MessageFeedback({ messageId, onFeedback, className }: MessageFeedbackProps) {
  const [rating, setRating] = useState<'thumbs_up' | 'thumbs_down' | null>(null);
  const [comment, setComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCommentOpen, setIsCommentOpen] = useState(false);

  const handleRating = async (newRating: 'thumbs_up' | 'thumbs_down') => {
    if (rating === newRating) return; // Already rated
    
    setRating(newRating);
    
    if (newRating === 'thumbs_up') {
      // For positive feedback, submit immediately
      await submitFeedback(newRating);
    } else {
      // For negative feedback, show comment popup
      setIsCommentOpen(true);
    }
  };

  const submitFeedback = async (feedbackRating: 'thumbs_up' | 'thumbs_down', feedbackComment?: string) => {
    if (!onFeedback) return;
    
    setIsSubmitting(true);
    try {
      await onFeedback(messageId, feedbackRating, feedbackComment);
      setIsCommentOpen(false);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      setRating(null); // Reset on error
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCommentSubmit = async () => {
    if (rating) {
      await submitFeedback(rating, comment);
    }
  };

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleRating('thumbs_up')}
        disabled={isSubmitting}
        className={cn(
          "h-6 w-6 p-0 hover:bg-green-100 hover:text-green-700",
          rating === 'thumbs_up' && "bg-green-100 text-green-700"
        )}
      >
        <ThumbsUp className="h-3 w-3" />
      </Button>

      <Popover open={isCommentOpen} onOpenChange={setIsCommentOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleRating('thumbs_down')}
            disabled={isSubmitting}
            className={cn(
              "h-6 w-6 p-0 hover:bg-red-100 hover:text-red-700",
              rating === 'thumbs_down' && "bg-red-100 text-red-700"
            )}
          >
            <ThumbsDown className="h-3 w-3" />
          </Button>
        </PopoverTrigger>
        
        <PopoverContent className="w-80" side="top">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              <h4 className="text-sm font-medium">Help us improve</h4>
            </div>
            
            <p className="text-xs text-muted-foreground">
              What could have been better about this response?
            </p>
            
            <Textarea
              placeholder="Your feedback helps us improve our responses..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="text-sm min-h-[80px] resize-none"
            />
            
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsCommentOpen(false);
                  setRating(null);
                  setComment("");
                }}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleCommentSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? "Submitting..." : "Submit"}
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
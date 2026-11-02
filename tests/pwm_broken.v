// Deliberate negative fixture: <= adds an unintended high sample at 0% duty.
module pwm_demo #(parameter STEP_PERIODS=4096)(input wire clk,rst,output wire led);
    localparam FRAME_BITS=(STEP_PERIODS>1)?$clog2(STEP_PERIODS):1;
    reg [7:0] phase;
    reg [FRAME_BITS-1:0] frames;
    reg [2:0] stage;
    wire [8:0] duty={stage,6'b0};
    always @(posedge clk) begin
        if(rst)begin phase<=0;frames<=0;stage<=0;end
        else begin
            phase<=phase+1'b1;
            if(phase==255)begin
                if(frames==STEP_PERIODS-1)begin
                    frames<=0;stage<=(stage==4)?0:stage+1'b1;
                end else frames<=frames+1'b1;
            end
        end
    end
    assign led=!rst && ({1'b0,phase}<=duty);
endmodule

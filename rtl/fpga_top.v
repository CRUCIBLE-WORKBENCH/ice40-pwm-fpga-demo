module fpga_top(input wire clk,output wire led);
    // iCE40 configuration initializes this register to zero. Seven clock edges
    // synchronously reset the engine; no unassigned external reset pin exists.
    reg [2:0] startup=0;
    wire rst=(startup!=7);
    always @(posedge clk)if(rst)startup<=startup+1'b1;
    pwm_demo #(.STEP_PERIODS(4096)) engine(.clk(clk),.rst(rst),.led(led));
endmodule

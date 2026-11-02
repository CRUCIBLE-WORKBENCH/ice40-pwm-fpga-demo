`timescale 1ns/1ps
module tb;
    parameter STEP_PERIODS=2;
    reg clk=0,rst=1;
    wire led;
    pwm_demo #(.STEP_PERIODS(STEP_PERIODS)) dut(.clk(clk),.rst(rst),.led(led));
    always #5 clk=~clk;
    integer cycles=0,checks=0,elapsed=0,phase,stage,duty,expected;
    integer high_count=0,periods=0,seen[0:4];
    integer i;
    task tick;
        input reset_value;
        begin
            @(negedge clk);rst=reset_value;
            @(posedge clk);#1;
            if(reset_value) begin elapsed=0;high_count=0;end
            else elapsed=elapsed+1;
            phase=elapsed%256;
            stage=(elapsed/(256*STEP_PERIODS))%5;
            duty=stage*64;
            expected=(!reset_value && phase<duty);
            if(led!==expected[0]) begin
                $display("PWM_MISMATCH cycle=%0d elapsed=%0d phase=%0d stage=%0d duty=%0d got=%b expected=%b",cycles,elapsed,phase,stage,duty,led,expected[0]);
                $fatal(1,"PWM independent sample mismatch");
            end
            if(!reset_value) begin
                // Starting at phase zero gives a whole 256-sample period.
                if(phase==0)high_count=0;
                if(led)high_count=high_count+1;
                if(phase==255 && elapsed>=256) begin
                    if(high_count!=duty)$fatal(1,"PWM period duty mismatch");
                    checks=checks+1;periods=periods+1;seen[stage]=seen[stage]+1;
                end
            end
            cycles=cycles+1;checks=checks+1;
        end
    endtask
    initial begin
        for(i=0;i<5;i=i+1)seen[i]=0;
        tick(1);
        repeat(6000)tick(0);
        tick(1);
        repeat(255)tick(0);
        tick(1); // Reset one edge before a period boundary.
        repeat(2561)tick(0);
        tick(1);
        repeat(1300)tick(0);
        for(i=0;i<5;i=i+1)if(seen[i]==0)$fatal(1,"PWM stage not exercised");
        $display("PWM_CORE_PASS cycles=%0d checks=%0d full_periods=%0d",cycles,checks,periods);
        $finish;
    end
endmodule
